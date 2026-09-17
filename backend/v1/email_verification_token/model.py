from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.core import Base


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(minutes=30),
        nullable=False,
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
