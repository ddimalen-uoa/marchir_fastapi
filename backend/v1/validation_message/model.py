from __future__ import annotations
from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.core import Base

class ValidationMesage(Base):
    __tablename__ = 'validation_message'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self):
        return f"<ValidationMesage(name='{self.name}')>"