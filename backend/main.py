from fastapi import FastAPI
from config.core import engine, Base
from api import register_routes
from logger import configure_logging, LogLevels

import v1.models

configure_logging(LogLevels.info)

app = FastAPI(
    root_path="/api"
)

@app.get("/healthz")
def healthz():
    return {"ok": True}

Base.metadata.create_all(bind=engine)

register_routes(app)