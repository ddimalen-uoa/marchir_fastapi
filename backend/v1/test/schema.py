from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

class TestResponse(BaseModel):
    id: UUID
    name: str
    value: str

    model_config = ConfigDict(from_attributes=True)

class AddTestRequest(BaseModel):
    name: str
    value: str