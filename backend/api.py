from fastapi import FastAPI
from v1.test.controller import router as test_router


def register_routes(app: FastAPI):
    app.include_router(test_router, prefix="/v1")
