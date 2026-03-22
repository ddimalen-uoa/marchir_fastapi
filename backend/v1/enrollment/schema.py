from typing import Optional
from datetime import date

from pydantic import BaseModel, ConfigDict

class CourseListItemResponse(BaseModel):
    id: int
    name: Optional[str]
    course_code: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    is_active: bool
    enrolled_students: int

    model_config = ConfigDict(from_attributes=True)