from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

import uuid
from config.core import Base

class TestTable(Base):
    __tablename__ = 'test_table'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name =  Column(String, nullable=False)
    value =  Column(String, nullable=True)

    def __repr__(self):
        return f"<TestTable(name='{self.name}')>"    