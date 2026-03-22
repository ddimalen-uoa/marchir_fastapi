from fastapi import APIRouter, status,  UploadFile, File, HTTPException, Form
from fastapi.responses import PlainTextResponse
from config.core import DbSession

from datetime import datetime
from typing import Optional

from . import service
from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment, AdminMember

router = APIRouter(
    prefix='/course-route',
    tags=['Course Route']
)

@router.post("/add-course")
async def add_course_route(
    member: AdminMember,
    name: Optional[str] = Form(None),
    course_code: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    is_active: bool = Form(True),
    db: DbSession = None
):
    return await service.add_course(member, name, course_code, start_date, end_date, is_active, db)

@router.put("/edit-course/{course_id}")
async def edit_course_route(
    member: AdminMember,
    course_id: int,
    name: Optional[str] = Form(None),
    course_code: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    is_active: bool = Form(True),    
    db: DbSession = None
):
    return await service.edit_course(member, course_id, name, course_code, start_date, end_date, is_active, db)