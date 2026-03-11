from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.core import Base

class OAuthTransaction(Base):
    __tablename__ = "oauth_transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    state: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    code_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(minutes=10),
        nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)