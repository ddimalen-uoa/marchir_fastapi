from sqlalchemy import Column, String
from config.core import Base

class Uploaded(Base):
    __tablename__ = 'uploaded'

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name =  Column(String, nullable=True)
    upi =  Column(String(20), nullable=True)


    def __repr__(self):
        return f"<Uploaded(name='{self.file_name}')>"    