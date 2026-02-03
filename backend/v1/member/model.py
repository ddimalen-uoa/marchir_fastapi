import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from config.core import Base


class Member(Base):
    __tablename__ = "member"

    id = Column(Integer, primary_key=True, autoincrement=True)

    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100))
    upi = Column(String(20))
    employee_id = Column(String(50))
    image_file = Column(String(500))

    notification_type = Column(Integer)
    role = Column(String(200))

    created = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
    last_edited = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)

    request_members = relationship(
        "RequestMember",
        back_populates="member",
        cascade="all, delete-orphan",
    )

    # many-to-many with Request through request_member association table
    requests = relationship(
        "Request",
        secondary="request_member",
        back_populates="members",
    )

    def __repr__(self):
        return f"<Member(id={self.id}, email={self.email!r})>"