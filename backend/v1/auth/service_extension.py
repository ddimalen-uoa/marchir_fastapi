from datetime import datetime

from fastapi import Cookie, HTTPException, Depends
from typing import Annotated
from collections.abc import Callable

from config.core import DbSession
from v1.user_session.model import UserSession
from v1.member.model import Member
from v1.enrollment.model import Enrollment
from v1.course.model import Course


def get_current_member(
    db: DbSession,
    session_token: str | None = Cookie(default=None),
) -> Member:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_row = (
        db.query(UserSession)
        .filter(UserSession.session_token == session_token)
        .first()
    )

    if not session_row:
        raise HTTPException(status_code=401, detail="Invalid session")

    if session_row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Session expired")

    member = session_row.member
    if not member:
        raise HTTPException(status_code=401, detail="Member not found")

    return member


CurrentMember = Annotated[Member, Depends(get_current_member)]

def require_roles(*allowed_roles: str) -> Callable:
    def role_checker(member: CurrentMember) -> Member:
        if not member.role:
            raise HTTPException(status_code=403, detail="User has no role assigned")

        member_role = member.role.strip().lower()
        normalized_allowed_roles = {role.strip().lower() for role in allowed_roles}

        if member_role not in normalized_allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource",
            )

        return member

    return role_checker

StudentMember = Annotated[Member, Depends(require_roles("student"))]
TeacherMember = Annotated[Member, Depends(require_roles("teacher"))]
AdminMember = Annotated[Member, Depends(require_roles("admin"))]

def get_current_enrollment(
    member: StudentMember,
    db: DbSession
) -> Enrollment:

    enrollment = (
        db.query(Enrollment)
        .join(Course)
        .filter(
            Enrollment.member_id == member.id,
            Course.is_active == True
        )
        .first()
    )

    if not enrollment:
        raise HTTPException(
            status_code=403,
            detail="Student has no active enrollment"
        )

    return enrollment

CurrentEnrollment = Annotated[
    Enrollment,
    Depends(get_current_enrollment)
]