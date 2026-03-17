from fastapi import FastAPI

from v1.test.controller import router as test_router
from v1.uploaded.controller import router as uploaded_router
from v1.enrollment.controller import router as enrollment_router
from v1.auth.controller import router as auth_router
from v1.marker_result.controller import router as marker_result_router

def register_routes(app: FastAPI):
    app.include_router(test_router, prefix="/v1")
    app.include_router(uploaded_router, prefix="/v1")
    app.include_router(enrollment_router, prefix="/v1")
    app.include_router(auth_router, prefix="/v1")
    app.include_router(marker_result_router, prefix="/v1")