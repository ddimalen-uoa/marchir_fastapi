from fastapi import APIRouter, Cookie
from pydantic import BaseModel, EmailStr
from config.core import DbSession

from . import service
from v1.auth.service_extension import CurrentMember

router = APIRouter(
    prefix='/auth',
    tags=['Authentication Route']
)


class EmailLoginRequest(BaseModel):
    email: EmailStr


@router.get("/config")
async def get_auth_config_route():
    return await service.get_auth_config_module()


@router.get("/login")
async def get_login_route(
    db:DbSession,    # type: ignore
    provider: str | None = None,
):
    return await service.get_login_module(db, provider)

@router.get("/callback")
async def get_callback_route(
    db: DbSession = None, # type: ignore
    code: str | None = None, 
    state: str | None = None    
):
    return await service.get_callback_module(db, code, state)


@router.post("/email/login")
async def post_email_login_route(
    request: EmailLoginRequest,
    db: DbSession = None, # type: ignore
):
    return await service.post_email_login_module(db, str(request.email))


@router.get("/email/verify")
async def get_email_verify_route(
    db: DbSession = None, # type: ignore
    token: str | None = None,
):
    return await service.get_email_verify_module(db, token)


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
