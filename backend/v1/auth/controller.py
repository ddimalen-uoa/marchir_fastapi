from fastapi import APIRouter, Cookie, Request
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from config.config_loader import settings
from rate_limiting import limiter
from v1.auth.admin_session import ADMIN_COOKIE, ADMIN_SESSION_SECONDS, authenticate_admin, create_admin_token
from config.core import DbSession

from . import service
from v1.auth.service_extension import CurrentMember, AdminMember
from v1.auth.messages import AccountSuspendedError


def suspended_login_response(error: AccountSuspendedError):
    response = RedirectResponse(service.get_frontend_login_url(error.detail), status_code=302)
    response.delete_cookie("session_token")
    return response

router = APIRouter(
    prefix='/auth',
    tags=['Authentication Route']
)


class EmailLoginRequest(BaseModel):
    email: EmailStr
    course_id: int | None = None


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=256)
    password: str = Field(min_length=1, max_length=1024)


@router.post("/admin/login")
@limiter.limit("5/minute")
async def post_admin_login_route(request: Request, credentials: AdminLoginRequest):
    admin = authenticate_admin(credentials.username, credentials.password)
    response = JSONResponse({"authenticated": True, "admin": admin.model_dump()})
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        key=ADMIN_COOKIE,
        value=create_admin_token(),
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="strict",
        max_age=ADMIN_SESSION_SECONDS,
    )
    return response


@router.get("/admin/me")
async def get_admin_me_route(admin: AdminMember):
    return JSONResponse(
        {"authenticated": True, "admin": admin.model_dump()},
        headers={"Cache-Control": "no-store"},
    )


@router.post("/admin/logout")
async def post_admin_logout_route():
    response = JSONResponse({"ok": True})
    response.delete_cookie(ADMIN_COOKIE, samesite="strict", secure=settings.APP_ENV == "production", httponly=True)
    return response


@router.get("/config")
async def get_auth_config_route():
    return await service.get_auth_config_module()


@router.get("/login")
async def get_login_route(
    db:DbSession,    # type: ignore
    provider: str | None = None,
    course_id: int | None = None,
):
    return await service.get_login_module(db, provider, course_id)

@router.get("/callback")
async def get_callback_route(
    db: DbSession = None, # type: ignore
    code: str | None = None, 
    state: str | None = None    
):
    try:
        return await service.get_callback_module(db, code, state)
    except AccountSuspendedError as error:
        return suspended_login_response(error)


@router.post("/email/login")
async def post_email_login_route(
    request: EmailLoginRequest,
    db: DbSession = None, # type: ignore
):
    return await service.post_email_login_module(db, str(request.email), request.course_id)


@router.get("/email/verify")
async def get_email_verify_route(
    db: DbSession = None, # type: ignore
    token: str | None = None,
):
    try:
        return await service.get_email_verify_module(db, token)
    except AccountSuspendedError as error:
        return suspended_login_response(error)


@router.get("/me")
async def get_me_route(
    member: CurrentMember
):
    return await service.get_me_module(member)

@router.post("/logout")
async def get_logout_route(
    session_token: str | None = Cookie(default=None),
    db: DbSession = None, # type: ignore
):
    return await service.get_logout_module(session_token, db)
