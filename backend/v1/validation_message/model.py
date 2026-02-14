from sqlalchemy import Column, String, Integer
from config.core import Base

class ValidationMesage(Base):
    __tablename__ = 'validation_message'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name =  Column(String, nullable=False)
    code =  Column(String, nullable=True)
    Message =  Column(String, nullable=True)

    def __repr__(self):
        return f"<TestTable(name='{self.name}')>"    