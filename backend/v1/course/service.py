import os
from datetime import datetime
from fastapi import Form, HTTPException


from typing import List, Any, Optional

from config.core import DbSession
from v1.auth.service_extension import CurrentMember, StudentMember, CurrentEnrollment, AdminMember

from config.config_loader import settings

from v1.course.model import Course

async def add_course(
    member: AdminMember,
    name: Optional[str] = Form(None),
    course_code: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    is_active: bool = Form(True),    
    db: DbSession = None
):
    try:
        parsed_start_date = (
            datetime.fromisoformat(start_date) if start_date else None
        )
        parsed_end_date = (
            datetime.fromisoformat(end_date) if end_date else None
        )

        course = Course(
            name=name,
            course_code=course_code,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            is_active=is_active,
        )

        db.add(course)
        db.commit()
        db.refresh(course)

        return {
            "ok": True,
            "message": "Course created successfully",
            "course": {
                "id": course.id,
                "name": course.name,
                "course_code": course.course_code,
                "start_date": course.start_date.isoformat() if course.start_date else None,
                "end_date": course.end_date.isoformat() if course.end_date else None,
                "is_active": course.is_active,
            },
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use ISO format like 2026-03-22T09:00:00"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def edit_course(
    member: AdminMember,
    course_id: int,    
    name: Optional[str] = Form(None),
    course_code: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    is_active: bool = Form(True),    
    db: DbSession = None
):
    print('Here at 77')
    try:
        course = db.query(Course).filter(Course.id == course_id).first()

        print('Here we go')
        print(course)

        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        course.name = name
        course.course_code = course_code
        course.start_date = datetime.fromisoformat(start_date) if start_date else None
        course.end_date = datetime.fromisoformat(end_date) if end_date else None
        course.is_active = is_active

        db.commit()
        db.refresh(course)

        return {
            "ok": True,
            "message": "Course updated successfully",
            "course": {
                "id": course.id,
                "name": course.name,
                "course_code": course.course_code,
                "start_date": course.start_date.isoformat() if course.start_date else None,
                "end_date": course.end_date.isoformat() if course.end_date else None,
                "is_active": course.is_active,
            },
        }

    except ValueError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use ISO format like 2026-03-22T09:00:00",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))