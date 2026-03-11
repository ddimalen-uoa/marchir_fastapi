from fastapi import FastAPI

from starlette.middleware.sessions import SessionMiddleware

from config.core import engine, Base
from api import register_routes
from logger import configure_logging, LogLevels

import v1.models

configure_logging(LogLevels.info)

SESSION_SECRET = "change-me-in-production"

app = FastAPI(
    root_path="/api"
)

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

register_routes(app)