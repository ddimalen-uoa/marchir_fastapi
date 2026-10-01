from fastapi import FastAPI

from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import text

from config.core import engine, Base, SessionLocal
from api import register_routes
from logger import configure_logging, LogLevels
from v1.course.current import ensure_current_hci_course
from rate_limiting import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import v1.models

configure_logging(LogLevels.info)

SESSION_SECRET = "change-me-in-production"

app = FastAPI(
    root_path="/api"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="app_session",
    same_site="lax",   # often OK for same-site frontend/backend usage
    https_only=False,  # True in production with HTTPS
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

Base.metadata.create_all(bind=engine)


def ensure_auth_schema():
    statements = [
        "ALTER TABLE member ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50)",
        "ALTER TABLE member ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE member ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP",
        "ALTER TABLE oauth_transaction ADD COLUMN IF NOT EXISTS provider VARCHAR(50) NOT NULL DEFAULT 'sso'",
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


ensure_auth_schema()


def ensure_current_hci_course_on_startup():
    db = SessionLocal()
    try:
        ensure_current_hci_course(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


ensure_current_hci_course_on_startup()

register_routes(app)
