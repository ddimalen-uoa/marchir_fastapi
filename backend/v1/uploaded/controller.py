from fastapi import APIRouter, status,  UploadFile, File, HTTPException

from config.core import DbSession

from . import service
from v1.auth.service_extension import CurrentMember, StudentMember

router = APIRouter(
    prefix='/upload-route',
    tags=['Upload Route']
)


@router.post("/upload-zip")
async def upload_zip_route(
    member: StudentMember,
    file: UploadFile = File(...),    
    db: DbSession = None # type: ignore    
):
    return await service.upload_zip(
        member,
        file,
        db
    )


@router.post("/test-me")
async def test_me_route():
    return await service.test_me()