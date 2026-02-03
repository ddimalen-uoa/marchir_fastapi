from fastapi import APIRouter, status,  UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
from config.core import DbSession

from . import service
from . import schema

router = APIRouter(
    prefix='/test-route',
    tags=['Test Route']
)

@router.get("/", status_code=status.HTTP_200_OK)
def get_test_module(db: DbSession):
    return service.get_test_module(db)

@router.post(
        "/add-test", 
        response_model=schema.TestResponse,
        status_code=status.HTTP_201_CREATED,
)
async def add_test(
    db: DbSession, 
    add_test_request: schema.AddTestRequest,
):
    return service.add_test(db, add_test_request)

@router.post("/upload-zip", response_class=PlainTextResponse)
async def upload_zip_route(file: UploadFile = File(...)):
    return await service.upload_zip(file)