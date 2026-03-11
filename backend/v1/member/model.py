from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from v1.enrollment.model import Enrollment

from config.core import Base

class Member(Base):
    __tablename__ = "member"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    upi: Mapped[Optional[str]] = mapped_column(
        String(20),
        index=True,
        unique=True,
        nullable=True,
    )
    role: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    created: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True
    )
    last_edited: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True, onupdate=datetime.utcnow
    )
    
    # Relationship
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Member(id={self.id}, email={self.email!r})>"