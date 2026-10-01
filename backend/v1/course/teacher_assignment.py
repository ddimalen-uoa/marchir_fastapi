from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core import Base
from v1.course.model import Course


class TeacherCourseAssignment(Base):
    __tablename__ = "teacher_course_assignment"
    __table_args__ = (UniqueConstraint("member_id", "course_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("course.id"), nullable=False, index=True)
    course: Mapped[Course] = relationship("Course")
