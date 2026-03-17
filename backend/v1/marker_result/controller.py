from fastapi import APIRouter, status,  UploadFile, File, HTTPException

from config.core import DbSession

from . import service
from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment

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