import logger
from fastapi import HTTPException

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

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