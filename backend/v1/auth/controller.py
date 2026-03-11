from fastapi import APIRouter, Cookie
from config.core import DbSession

from . import service

router = APIRouter(
    prefix='/auth',
    tags=['Authentication Route']
)

@router.get("/login")
async def get_login_route(
    db:DbSession    # type: ignore
):
    return await service.get_login_module(db)

@router.get("/callback")
async def get_callback_route(
    db: DbSession = None, # type: ignore
    code: str | None = None, 
    state: str | None = None    
):
    return await service.get_callback_module(db, code, state)

@router.get("/me")
async def get_me_route(
    session_token: str | None = Cookie(default=None),
    db: DbSession = None, # type: ignore
):
    return await service.get_me_module(session_token, db)

@router.post("/logout")
async def get_logout_route(
    session_token: str | None = Cookie(default=None),
    db: DbSession = None, # type: ignore
):
    return await service.get_logout_module(session_token, db)