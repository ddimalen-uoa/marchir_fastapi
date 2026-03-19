import logger
from fastapi import HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse
import shutil

import csv
import io
import json
from datetime import datetime

from pathlib import Path

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, joinedload

from config.core import DbSession

from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment, TeacherMember

from v1.course.model import Course
from v1.enrollment.model import Enrollment
from v1.member.model import Member
from v1.marker_result.model import MarkerResult

async def get_last_submission(
        member: StudentMember,
        enrollment: CurrentEnrollment,
        db: DbSession = None # type: ignore
    ):

    last_submission = db.query(MarkerResult).filter(
            MarkerResult.enrollment_id == enrollment.id
        ).first()

    return last_submission

async def get_active_courses_with_students_and_submissions(
    member: TeacherMember,
    db: DbSession = None
) -> dict[str, Any]:
    stmt = (    
        select(Course)
        .where(Course.is_active.is_(True))
        .options(
            selectinload(Course.enrollments)
            .selectinload(Enrollment.member),
            selectinload(Course.enrollments)
            .selectinload(Enrollment.marker_results),
        )
        .order_by(Course.id)
    )

    courses = db.scalars(stmt).all()

    response = {"courses": []}

    for course in courses:
        students = []
        submitted_students = []

        for enrollment in course.enrollments:
            member = enrollment.member

            if not member or (member.role or "").lower() != "student":
                continue

            student_data = {
                "member_id": member.id,
                "upi": member.upi,
                "first_name": member.first_name,
                "last_name": member.last_name,
                "email": member.email,
            }
            students.append(student_data)

            if enrollment.marker_results:
                latest_submission = max(
                    enrollment.marker_results,
                    key=lambda mr: mr.submitted_at
                )

                submitted_students.append({
                    **student_data,
                    "submission": {
                        "marker_result_id": latest_submission.id,
                        "file_name": latest_submission.file_name,
                        "validation_result": latest_submission.validation_result,
                        "result": latest_submission.result,
                        "status": latest_submission.status,
                        "submitted_at": latest_submission.submitted_at.isoformat(),
                    }
                })

        response["courses"].append({
            "id": course.id,
            "name": course.name,
            "course_code": course.course_code,
            "start_date": course.start_date.isoformat() if course.start_date else None,
            "end_date": course.end_date.isoformat() if course.end_date else None,
            "students": students,
            "submitted_students": submitted_students,
        })

    return response


async def download_zip_course(
        member: TeacherMember,
        course: str = Form(...),
        db: DbSession = None # type: ignore
    ):

    source_folder = Path(f"/marchir/uploads/{course}")
    output_zip = Path(f"/marchir/uploads/zipfiles/{course.replace(".", "")}.zip")

    output_zip.parent.mkdir(parents=True, exist_ok=True)

    zip_path = shutil.make_archive(
        base_name=str(output_zip),
        format="zip",
        root_dir=str(source_folder)
    )

    return FileResponse(
        path=zip_path,
        filename=f"{course.replace(".", "")}.zip",
        media_type="application/zip"
    )


async def download_course_marker_results_csv(
    member: TeacherMember,
    course_id: int,
    db: DbSession = None,  # type: ignore   
):

    # 1) Make sure course exists
    course = db.scalar(
        select(Course).where(Course.id == course_id)
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 2) Load all enrollments for this course, including member and marker results
    enrollments = db.scalars(
        select(Enrollment)
        .where(Enrollment.course_id == course_id)
        .options(
            joinedload(Enrollment.member),
            joinedload(Enrollment.marker_results),
        )
    ).unique().all()

    # 3) First pass: collect all JSON keys used in marker_result.result
    dynamic_keys: set[str] = set()

    for enrollment in enrollments:
        marker_result = None

        # If there should only be one per enrollment, use the latest one just in case
        if enrollment.marker_results:
            marker_result = max(
                enrollment.marker_results,
                key=lambda x: x.submitted_at or datetime.min
            )

        if marker_result and marker_result.result:
            try:
                parsed = json.loads(marker_result.result)
                if isinstance(parsed, dict):
                    dynamic_keys.update(parsed.keys())
            except json.JSONDecodeError:
                pass

    # Optional: keep dynamic columns sorted for consistent CSV output
    dynamic_columns = sorted(dynamic_keys)

    # 4) CSV headers
    base_columns = ["first_name", "last_name", "upi", "email"]
    extra_columns = [
        "file_name",
        "validation_result",
        "status",
        "submitted_at",
    ]
    fieldnames = base_columns + extra_columns + dynamic_columns

    # 5) Write CSV into memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for enrollment in enrollments:
        member = enrollment.member
        marker_result = None

        if enrollment.marker_results:
            marker_result = max(
                enrollment.marker_results,
                key=lambda x: x.submitted_at or datetime.min
            )

        row: dict[str, Any] = {
            "first_name": member.first_name if member else "",
            "last_name": member.last_name if member else "",
            "upi": member.upi if member else "",
            "email": member.email if member else "",
            "file_name": "",
            "validation_result": "",
            "status": "",
            "submitted_at": "",
        }

        # Default all dynamic columns to empty
        for col in dynamic_columns:
            row[col] = ""

        if marker_result:
            row["file_name"] = marker_result.file_name or ""
            row["validation_result"] = marker_result.validation_result or ""
            row["status"] = marker_result.status or ""
            row["submitted_at"] = (
                marker_result.submitted_at.isoformat()
                if marker_result.submitted_at else ""
            )

            if marker_result.result:
                try:
                    parsed = json.loads(marker_result.result)
                    if isinstance(parsed, dict):
                        for key, value in parsed.items():
                            row[key] = value
                except json.JSONDecodeError:
                    # if result is not valid JSON, leave dynamic columns empty
                    pass

        writer.writerow(row)

    output.seek(0)

    # 6) Return downloadable CSV
    filename = f"{(course.course_code or course.name or f'course_{course.id}').replace('.', '').replace(' ', '_')}_marker_results.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )    