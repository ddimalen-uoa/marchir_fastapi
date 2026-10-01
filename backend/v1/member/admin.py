from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from config.core import DbSession
from v1.auth.service_extension import AdminMember
from v1.course.model import Course
from v1.course.teacher_assignment import TeacherCourseAssignment
from v1.email_verification_token.model import EmailVerificationToken
from v1.enrollment.model import Enrollment
from v1.marker_result.model import MarkerResult
from v1.member.model import Member
from v1.user_session.model import UserSession

router = APIRouter(prefix="/admin/users", tags=["Admin users"])


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=100)
    upi: str | None = Field(default=None, max_length=20)
    role: Literal["student", "teacher"] | None = None
    is_active: bool | None = None

    @field_validator("first_name", "last_name", "upi", mode="before")
    @classmethod
    def normalize_text(cls, value):
        return value.strip() or None if isinstance(value, str) else value


class CourseMove(BaseModel):
    enrollment_id: int | None = Field(default=None, gt=0)
    course_id: int = Field(gt=0)


class TeacherCoursesUpdate(BaseModel):
    course_ids: list[int] = Field(max_length=500)

    @field_validator("course_ids")
    @classmethod
    def validate_ids(cls, values):
        if any(value <= 0 for value in values):
            raise ValueError("Course IDs must be positive.")
        return sorted(set(values))


def serialize_user(member: Member, submission_ids: set[int], assignments: list[TeacherCourseAssignment]):
    return {
        "id": member.id, "first_name": member.first_name, "last_name": member.last_name,
        "email": member.email, "upi": member.upi, "role": member.role,
        "is_active": member.is_active, "email_verified": member.email_verified,
        "created": member.created,
        "teacher_courses": [
            {"id": item.course_id, "name": item.course.name, "course_code": item.course.course_code, "is_active": item.course.is_active}
            for item in assignments
        ] if member.role == "teacher" else [],
        "enrollments": [
            {"id": item.id, "course_id": item.course_id, "course_name": item.course.name,
             "course_code": item.course.course_code, "has_submission": item.id in submission_ids}
            for item in sorted(member.enrollments, key=lambda item: (item.course.name or "", item.id))
        ],
    }


@router.get("")
def list_users(
    admin: AdminMember, db: DbSession,
    search: str = Query(default="", max_length=200),
    course_id: int | None = Query(default=None, gt=0),
    role: Literal["student", "teacher"] | None = None,
    active: bool | None = None,
    submission: Literal["yes", "no"] | None = None,
    unenrolled: bool = False,
    sort: Literal["name", "email", "role", "course", "created"] = "name",
    direction: Literal["asc", "desc"] = "asc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    query = db.query(Member)
    term = search.strip()
    if term:
        pattern = "%" + term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        full_name = func.coalesce(Member.first_name, "") + " " + func.coalesce(Member.last_name, "")
        query = query.filter(or_(*[column.ilike(pattern, escape="\\") for column in
                                  (Member.first_name, Member.last_name, Member.email, Member.upi, full_name)]))
    if role:
        query = query.filter(Member.role == role)
    if active is not None:
        query = query.filter(Member.is_active == active)
    if unenrolled:
        assigned = select(TeacherCourseAssignment.id).where(TeacherCourseAssignment.member_id == Member.id).exists()
        query = query.filter(case((Member.role == "teacher", ~assigned), else_=~Member.enrollments.any()))
    if course_id:
        assigned = select(TeacherCourseAssignment.id).where(TeacherCourseAssignment.member_id == Member.id, TeacherCourseAssignment.course_id == course_id).exists()
        query = query.filter(case((Member.role == "teacher", assigned), else_=Member.enrollments.any(Enrollment.course_id == course_id)))
    submitted = select(MarkerResult.id).join(Enrollment).where(Enrollment.member_id == Member.id)
    if course_id:
        submitted = submitted.where(Enrollment.course_id == course_id)
    if submission:
        query = query.filter(submitted.exists() if submission == "yes" else ~submitted.exists())
    total = query.count()
    course_sort = select(func.min(Course.name)).join(Enrollment, Enrollment.course_id == Course.id).where(Enrollment.member_id == Member.id).scalar_subquery()
    teacher_course_sort = select(func.min(Course.name)).join(TeacherCourseAssignment, TeacherCourseAssignment.course_id == Course.id).where(TeacherCourseAssignment.member_id == Member.id).scalar_subquery()
    sorts = {
        "name": func.lower(func.coalesce(Member.first_name, "") + " " + func.coalesce(Member.last_name, "")),
        "email": func.lower(Member.email), "role": Member.role,
        "course": case((Member.role == "teacher", teacher_course_sort), else_=course_sort), "created": Member.created,
    }
    order = sorts[sort].desc() if direction == "desc" else sorts[sort].asc()
    members = query.options(selectinload(Member.enrollments).selectinload(Enrollment.course)).order_by(order.nullslast(), Member.id).offset((page - 1) * page_size).limit(page_size).all()
    enrollment_ids = [item.id for member in members for item in member.enrollments]
    submission_ids = set(db.scalars(select(MarkerResult.enrollment_id).where(MarkerResult.enrollment_id.in_(enrollment_ids)))) if enrollment_ids else set()
    assignments = db.scalars(select(TeacherCourseAssignment).where(TeacherCourseAssignment.member_id.in_([member.id for member in members])).options(selectinload(TeacherCourseAssignment.course)).order_by(TeacherCourseAssignment.course_id)).all()
    assignments_by_member = {}
    for assignment in assignments:
        assignments_by_member.setdefault(assignment.member_id, []).append(assignment)
    return {"items": [serialize_user(member, submission_ids, assignments_by_member.get(member.id, [])) for member in members], "total": total, "page": page, "page_size": page_size}


@router.patch("/{member_id}")
def update_user(member_id: int, changes: UserUpdate, admin: AdminMember, db: DbSession):
    member = db.query(Member).filter(Member.id == member_id).with_for_update().first()
    if not member:
        raise HTTPException(status_code=404, detail="User not found.")
    values = changes.model_dump(exclude_unset=True)
    if any(values.get(key) is None for key in ("role", "is_active") if key in values):
        raise HTTPException(status_code=422, detail="User type and login status cannot be empty.")
    if "email" in values:
        values["email"] = str(values["email"]).lower() if values["email"] else None
    if "email" in values and values["email"] != member.email:
        member.email_verified = False
        member.email_verified_at = None
    revoke = values.get("is_active") is False or any(key in values and values[key] != getattr(member, key) for key in ("role", "email", "upi"))
    try:
        for key, value in values.items():
            setattr(member, key, value)
        if "role" in values and values["role"] != "teacher":
            db.query(TeacherCourseAssignment).filter(TeacherCourseAssignment.member_id == member.id).delete(synchronize_session=False)
        if revoke:
            db.query(UserSession).filter(UserSession.member_id == member.id).delete(synchronize_session=False)
            db.query(EmailVerificationToken).filter(EmailVerificationToken.member_id == member.id).update({"is_used": True}, synchronize_session=False)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That email address or UPI is already used.") from exc
    return {"ok": True}


@router.put("/{member_id}/teacher-courses")
def assign_teacher_courses(member_id: int, changes: TeacherCoursesUpdate, admin: AdminMember, db: DbSession):
    member = db.query(Member).filter(Member.id == member_id).with_for_update().first()
    if not member:
        raise HTTPException(status_code=404, detail="User not found.")
    if member.role != "teacher":
        raise HTTPException(status_code=400, detail="Only teachers can be assigned to teach courses.")
    existing = db.query(TeacherCourseAssignment).filter(TeacherCourseAssignment.member_id == member_id).all()
    existing_ids = {item.course_id for item in existing}
    requested = set(changes.course_ids)
    courses = db.query(Course).filter(Course.id.in_(requested)).all()
    if {course.id for course in courses} != requested:
        raise HTTPException(status_code=400, detail="One or more selected courses do not exist.")
    if any(not course.is_active and course.id not in existing_ids for course in courses):
        raise HTTPException(status_code=400, detail="New assignments must be to active courses.")
    for assignment in existing:
        if assignment.course_id not in requested:
            db.delete(assignment)
    for course_id in requested - existing_ids:
        db.add(TeacherCourseAssignment(member_id=member_id, course_id=course_id))
    db.commit()
    return {"ok": True}


@router.post("/{member_id}/course")
def move_user_course(member_id: int, move: CourseMove, admin: AdminMember, db: DbSession):
    member = db.query(Member).filter(Member.id == member_id).with_for_update().first()
    if not member:
        raise HTTPException(status_code=404, detail="User not found.")
    if member.role == "teacher":
        raise HTTPException(status_code=400, detail="Use teaching course assignments for teachers.")
    course = db.query(Course).filter(Course.id == move.course_id, Course.is_active.is_(True)).first()
    if not course:
        raise HTTPException(status_code=400, detail="Select an active destination course.")
    enrollment = None
    if move.enrollment_id is not None:
        enrollment = db.query(Enrollment).filter(Enrollment.id == move.enrollment_id, Enrollment.member_id == member_id).with_for_update().first()
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found for this user.")
        if enrollment.course_id == move.course_id:
            return {"ok": True}
        if db.query(MarkerResult.id).filter(MarkerResult.enrollment_id == enrollment.id).first():
            raise HTTPException(status_code=409, detail="This user has submitted an assignment for this course and cannot be moved.")
    if db.query(Enrollment.id).filter(Enrollment.member_id == member_id, Enrollment.course_id == move.course_id).first():
        raise HTTPException(status_code=409, detail="This user is already enrolled in the destination course.")
    if enrollment:
        enrollment.course_id = move.course_id
    else:
        db.add(Enrollment(member_id=member_id, course_id=move.course_id))
    db.commit()
    return {"ok": True}
