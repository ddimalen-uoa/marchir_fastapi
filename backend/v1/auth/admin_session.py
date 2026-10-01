import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel

from config.config_loader import settings

ADMIN_COOKIE = "admin_session_token"
ADMIN_SESSION_SECONDS = 8 * 60 * 60


class AdminIdentity(BaseModel):
    username: str
    role: str = "admin"


def admin_session_key() -> str:
    # Credential changes also invalidate previously issued admin sessions.
    credentials = f"{settings.ADMIN_USERNAME}\0{settings.ADMIN_PASSWORD}"
    return hmac.new(
        settings.SESSION_SECRET.encode(),
        b"admin-session\0" + credentials.encode(),
        hashlib.sha256,
    ).hexdigest()


def authenticate_admin(username: str, password: str) -> AdminIdentity:
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Admin login is not configured.")
    username_matches = secrets.compare_digest(username.encode(), settings.ADMIN_USERNAME.encode())
    password_matches = secrets.compare_digest(password.encode(), settings.ADMIN_PASSWORD.encode())
    if not (username_matches and password_matches):
        raise HTTPException(status_code=401, detail="Invalid admin username or password.")
    return AdminIdentity(username=settings.ADMIN_USERNAME)


def create_admin_token() -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": settings.ADMIN_USERNAME,
            "aud": "marchir-admin",
            "iat": now,
            "exp": now + timedelta(seconds=ADMIN_SESSION_SECONDS),
            "jti": secrets.token_urlsafe(24),
        },
        admin_session_key(),
        algorithm="HS256",
    )


def get_current_admin(
    admin_session_token: str | None = Cookie(default=None),
) -> AdminIdentity:
    if not admin_session_token or not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Admin sign-in required.")
    try:
        claims = jwt.decode(
            admin_session_token,
            admin_session_key(),
            algorithms=["HS256"],
            audience="marchir-admin",
            options={"require_exp": True, "require_sub": True, "require_aud": True},
        )
        if claims["sub"] != settings.ADMIN_USERNAME:
            raise JWTError("Invalid admin identity")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Admin session is invalid or expired.") from exc
    return AdminIdentity(username=settings.ADMIN_USERNAME)
