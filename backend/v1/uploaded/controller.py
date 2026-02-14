from fastapi import APIRouter, status,  UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
from config.core import DbSession

from . import service

router = APIRouter(
    prefix='/upload-route',
    tags=['Upload Route']
)


@router.post("/upload-zip", response_class=PlainTextResponse)
async def upload_zip_route(file: UploadFile = File(...)):
    return await service.upload_zip(file)


@router.post("/test-me", response_class=PlainTextResponse)
async def test_me_route():
    return await service.test_me()