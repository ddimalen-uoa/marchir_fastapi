from fastapi import APIRouter, status,  UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
from config.core import DbSession

from . import service
from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment, AdminMember

router = APIRouter(
    prefix='/enrollment-route',
    tags=['Enrollment Route']
)

@router.get("/auto-enroll")
async def get_auto_enroll_route(
    member: AdminMember,
    db: DbSession = None
):
    return await service.get_auto_enroll_module(member, db)