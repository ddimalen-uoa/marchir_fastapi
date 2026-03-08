import asyncio
import os
from datetime import datetime
from typing import List, Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from ldap3 import Server, Connection, ALL, SUBTREE

from config.config_loader import settings

from v1.course.model import Course
from v1.enrollment.model import Enrollment
from v1.member.model import Member


def is_semester_matched(semester: str, date_str: str, year: int) -> bool:
    """
    Compare a class start date against the expected semester window.
    """
    start_date = datetime.strptime(date_str, "%Y-%m-%d")

    if semester == "SS":
        semester_start = datetime(year, 1, 1)
        semester_mid = datetime(year, 1, 17)
    elif semester == "S1":
        semester_start = datetime(year, 2, 15)
        semester_mid = datetime(year, 3, 15)
    elif semester == "S2":
        semester_start = datetime(year, 7, 6)
        semester_mid = datetime(year, 9, 15)
    else:
        return False

    return semester_start < start_date < semester_mid


async def get_student_ids_from_enrolments(
    client: httpx.AsyncClient, class_id: str, year: int
) -> List[str]:
    headers = {"apikey": settings.API_TOKEN}
    params = {
        "classId": class_id,
        "acadYear": year,
        "offset": 0,
        "size": 500,
    }

    try:
        response = await client.get(settings.ENROLLMENT_API_URL, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        enrolments = data.get("_embedded", {}).get("enrolments", [])

        return [
            item.get("enrolment", {}).get("studentId")
            for item in enrolments
            if item.get("enrolment", {}).get("studentId") is not None
        ]

    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout while fetching enrolments for class {class_id}",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Enrolment API returned {e.response.status_code} for class {class_id}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Enrolment API request failed for class {class_id}: {str(e)}",
        )


async def get_course_numbers(
    client: httpx.AsyncClient,
    course_code: str,
    course_number: str,
    semester: str,
    year: int,
) -> List[str]:
    headers = {"apikey": settings.API_TOKEN}
    params = {
        "acadOrg": course_code,
        "catalogNbr": course_number,
        "year": year,
        "from": 0,
        "isActive": "true",
        "page": 0,
        "size": 500,
    }

    try:
        response = await client.get(settings.COURSE_API_URL, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        classes = data.get("data", [])

        course_number_array = []
        for item in classes:
            start_date = item.get("startDate")
            class_nbr = item.get("classNbr")

            if not start_date or not class_nbr:
                continue

            if is_semester_matched(semester, start_date, int(year)):
                course_number_array.append(class_nbr)

        return course_number_array

    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Timeout while fetching classes for {course_code}.{course_number}.{semester}.{year}",
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Classes API returned {e.response.status_code} for {course_code}.{course_number}.{semester}.{year}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Classes API request failed for {course_code}.{course_number}.{semester}.{year}: {str(e)}",
        )

async def get_upis_from_ldap(student_ids: list[str]) -> list[dict[str, Any]]:
    if not student_ids:
        return []

    return await asyncio.to_thread(_get_upis_from_ldap_sync, student_ids)

def _get_upis_from_ldap_sync(student_ids: list[str]) -> list[dict[str, Any]]:
    ldap_server_url = settings.LDAP_SERVER_URL
    user_dn = settings.LDAP_USER_DN
    password = settings.LDAP_PASSWORD

    server = Server(ldap_server_url, get_info=ALL)
    conn = None

    try:
        conn = Connection(server, user=user_dn, password=password, auto_bind=True)

        cn_filter = "".join(
            f"(employeeNumber={student_id})" for student_id in student_ids
        )
        ldap_filter = f"(&(objectCategory=user)(|{cn_filter}))"

        search_base = "ou=People,dc=UoA,dc=auckland,dc=ac,dc=nz"
        attributes = ["cn", "displayName", "givenName", "employeeNumber", "mail"]

        conn.search(
            search_base=search_base,
            search_filter=ldap_filter,
            search_scope=SUBTREE,
            attributes=attributes,
            paged_size=250,
        )

        student_data: list[dict[str, Any]] = []
        for entry in conn.entries:
            student_data.append(
                {
                    "UPI": entry.cn.value,
                    "DisplayName": entry.displayName.value,
                    "GivenName": entry.givenName.value,
                    "ID": entry.employeeNumber.value,
                    "Email": entry.mail.value,
                }
            )

        return student_data

    except Exception as e:
        # Better to log this properly in real code
        print(f"Error occurred during LDAP search: {e}")
        raise RuntimeError(f"LDAP search failed: {e}") from e

    finally:
        if conn is not None:
            conn.unbind()

def check_or_add_student(student, db: Session):
    stmt = select(Member).where(Member.upi == student["UPI"])
    existing_member = db.execute(stmt).scalar_one_or_none()

    if existing_member is not None:
        return existing_member.id
    
    new_member = Member(
        upi=student["UPI"],
        first_name=student["GivenName"],
        last_name=student["DisplayName"].replace(student["GivenName"], ""),
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    return new_member.id

async def process_course(
    client: httpx.AsyncClient,
    course_code: str,
    course_number: str,
    course_id: int,
    semester: str,
    year: int,
    db: Session
):
    class_numbers = await get_course_numbers(
        client, course_code, course_number, semester, year
    )

    student_ids = []
    for class_nbr in class_numbers:
        ids = await get_student_ids_from_enrolments(client, class_nbr, year)
        student_ids.extend(ids)

    # remove duplicates while keeping order
    student_ids = list(dict.fromkeys(str(student_id) for student_id in student_ids))

    student_list = await get_upis_from_ldap(student_ids)

    for student in student_list:
        member_id = check_or_add_student(student, db)
        stmt = select(Enrollment).where(
            Enrollment.member_id == member_id,
            Enrollment.course_id == course_id
        )
        student_enrolment = db.execute(stmt).scalar_one_or_none()
        if student_enrolment is None:
            student_enrolment = Enrollment(member_id=member_id, course_id=course_id)
            db.add(student_enrolment)
            db.commit()
            db.refresh(student_enrolment)

    return student_list


async def get_auto_enroll_module(db: Session):
    courses = db.query(Course).filter(Course.is_active).all()

    timeout = httpx.Timeout(20.0, connect=10.0)

    results = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for course in courses:
            parts = course.name.split(".")

            if len(parts) < 4:
                print(f"Skipping invalid course name format: {course.name}")
                continue

            course_code, course_number, semester, year = parts[0], parts[1], parts[2], parts[3]

            student_info = await process_course(
                client,
                course_code,
                course_number,
                course.id,
                semester,
                int(year),
                db
            )

            results.append(
                student_info
            )

    return results