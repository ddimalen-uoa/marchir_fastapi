from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import declarative_base
from fastapi import Depends
from tenacity import retry, wait_fixed, stop_after_attempt
from config.config_loader import settings
from typing import Annotated

@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def connect_to_db():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))  # ✅ use `text()` for raw SQL
    return engine

engine = connect_to_db()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DbSession = Annotated[Session, Depends(get_db)]