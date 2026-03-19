from fastapi import APIRouter, status,  UploadFile, File, HTTPException, Form

from config.core import DbSession
from typing import Any
from . import service
from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment, TeacherMember

router = APIRouter(
    prefix='/marker-result-route',
    tags=['Maker Result Route']
)


@router.get("/get-last-submission")
async def get_last_submission_route(
    member: StudentMember,
    enrollment: CurrentEnrollment,
    db: DbSession = None # type: ignore    
):
    return await service.get_last_submission(
        member,
        enrollment,
        db
    )

@router.get("/get-last-submission/active-with-students-and-submissions")
async def get_active_courses_with_students_and_submissions_route(
    member: TeacherMember,
    db: DbSession = None # type: ignore
) -> dict[str, Any]:
    return await service.get_active_courses_with_students_and_submissions(
        member,
        db
    )

@router.post("/download-zip-course")
async def download_zip_course_route(
    member: TeacherMember,
    course: str = Form(...),
    db: DbSession = None # type: ignore    
):
    return await service.download_zip_course(
        member,
        course,
        db
    )

@router.get("/download-marker-results-csv/{course_id}")
async def download_course_marker_results_csv_route(
    member: TeacherMember,
    course_id: int,
    db: DbSession = None,  # type: ignore
):
    return await service.download_course_marker_results_csv(
        member,
        course_id,
        db
    )