from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core import Base

if TYPE_CHECKING:
    from v1.enrollment.model import Enrollment

class Course(Base):
    __tablename__ = "course"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    course_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Course(id={self.id}, name={self.name!r})>"    