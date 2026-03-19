from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from v1.enrollment.model import Enrollment

from config.core import Base


class MarkerResult(Base):
    __tablename__ = 'marker_result'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollment.id"), nullable=False)

    file_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    validation_result: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    upi: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship""
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment",
        back_populates="marker_results"
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<MarkerResult(upi={self.upi})>"    