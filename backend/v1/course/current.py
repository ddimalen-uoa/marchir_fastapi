from datetime import date

from sqlalchemy import or_
from sqlalchemy.orm import Session

from config.config_loader import settings
from v1.course.model import Course
from v1.enrollment.model import Enrollment
from v1.member.model import Member


def is_google_auth_enabled() -> bool:
    return (settings.AUTH_PROVIDER or "").strip().lower() == "google"


def get_current_hci_course_code() -> str:
    return f"HCI-{date.today().year}"


def ensure_current_hci_course(db: Session) -> Course | None:
    if not is_google_auth_enabled():
        return None

    course_code = get_current_hci_course_code()
    course = (
        db.query(Course)
        .filter(
            or_(
                Course.name == course_code,
                Course.course_code == course_code,
            )
        )
        .first()
    )

    if course:
        return course

    course = Course(
        name=course_code,
        course_code=course_code,
        start_date=None,
        end_date=None,
        is_active=True,
    )
    db.add(course)
    db.flush()
    return course


def enroll_member_in_current_hci_course(
    db: Session,
    member: Member,
) -> Enrollment | None:
    if not is_google_auth_enabled():
        return None

    course = ensure_current_hci_course(db)
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.member_id == member.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )

    if enrollment:
        return enrollment

    enrollment = Enrollment(member_id=member.id, course_id=course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def get_active_course_by_id(db: Session, course_id: int) -> Course | None:
    return (
        db.query(Course)
        .filter(Course.id == course_id, Course.is_active.is_(True))
        .first()
    )


def enroll_member_in_course(
    db: Session,
    member: Member,
    course_id: int,
) -> Enrollment:
    course = get_active_course_by_id(db, course_id)
    if not course:
        raise ValueError("Selected course is not available")

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.member_id == member.id,
            Enrollment.course_id == course.id,
        )
        .first()
    )

    if enrollment:
        return enrollment

    enrollment = Enrollment(member_id=member.id, course_id=course.id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment
