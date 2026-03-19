from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core import Base  # <-- your FastAPI Base

if TYPE_CHECKING:
    from v1.member.model import Member
    from v1.course.model import Course
    from v1.marker_result.model import MarkerResult

class Enrollment(Base):
    __tablename__ = "enrollment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), nullable=False)

    # Relationship
    member: Mapped["Member"] = relationship(
        "Member", 
        back_populates="enrollments"
    )
    course: Mapped["Course"] = relationship(
        "Course", 
        back_populates="enrollments"
    )

    marker_results: Mapped[List["MarkerResult"]] = relationship(
        "MarkerResult",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Enrollment(id={self.id})>"
