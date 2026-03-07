from fastapi import APIRouter, status,  UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
from config.core import DbSession

from . import service

router = APIRouter(
    prefix='/enrollment-route',
    tags=['Enrollment Route']
)

@router.get("/auto-enroll")
async def get_auto_enroll_route(db: DbSession):
    return await service.get_auto_enroll_module(db)