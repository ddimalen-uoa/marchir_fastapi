from datetime import datetime, timedelta

from fastapi import HTTPException, Cookie
from fastapi.responses import RedirectResponse, JSONResponse

from sqlalchemy.orm import Session
from sqlalchemy import func

import secrets
import hashlib
import base64
import urllib.parse
import httpx

from v1.oauth_transaction.model import OAuthTransaction
from v1.member.model import Member
from v1.user_session.model import UserSession

from config.config_loader import settings

def extract_upi_from_email(email: str) -> str | None:
    if not email:
        return None

    if "@" not in email:
        return None

    return email.split("@")[0].lower()

def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)

def generate_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


async def get_login_module(db:Session):
    state = generate_state()
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    txn = OAuthTransaction(
        state=state,
        code_verifier=code_verifier,
        redirect_uri=settings.OAUTH_REDIRECT_URI,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        is_used=False,
    )
    db.add(txn)
    db.commit()

    params = {
        "response_type": "code",
        "client_id": settings.OAUTH_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "scope": "openid profile https://purchase.cs.auckland.ac.nz/read-data",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = settings.OAUTH_AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url, status_code=302)


async def get_callback_module(
        db: Session = None,
        code: str | None = None, 
        state: str | None = None
    ):
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    txn = (
        db.query(OAuthTransaction)
        .filter(OAuthTransaction.state == state)
        .first()
    )

    if not txn:
        raise HTTPException(status_code=400, detail="Invalid state")

    if txn.is_used:
        raise HTTPException(status_code=400, detail="State already used")

    if txn.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="State expired")

    token_payload = {
        "grant_type": "authorization_code",
        "client_id": settings.OAUTH_CLIENT_ID,
        "code": code,
        "redirect_uri": txn.redirect_uri,
        "code_verifier": txn.code_verifier,
    }

    if getattr(settings, "OAUTH_CLIENT_SECRET", None):
        token_payload["client_secret"] = settings.OAUTH_CLIENT_SECRET

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            settings.OAUTH_TOKEN_URL,
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Token exchange failed: {token_resp.text}",
            )

        tokens = token_resp.json()

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        id_token = tokens.get("id_token")
        token_type = tokens.get("token_type")
        scope = tokens.get("scope")

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token returned")

        userinfo_resp = await client.get(
            settings.OAUTH_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch user info: {userinfo_resp.text}",
            )

        userinfo = userinfo_resp.json()

    email = userinfo.get("email")

    if not email:
        raise HTTPException(status_code=403, detail="User account has no email")

    upi = extract_upi_from_email(email)

    if not upi:
        raise HTTPException(status_code=403, detail="Could not determine UPI")

    member = (
        db.query(Member)
        .filter(func.lower(Member.upi) == upi)
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Your account is not registered as a member.",
        )

    given_name = userinfo.get("given_name")
    family_name = userinfo.get("family_name")

    if not member.first_name and given_name:
        member.first_name = given_name

    if not member.last_name and family_name:
        member.last_name = family_name

    session_token = secrets.token_urlsafe(48)

    session_row = UserSession(
        session_token=session_token,
        member_id=member.id,
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=id_token,
        token_type=token_type,
        scope=scope,
        expires_at=datetime.utcnow() + timedelta(hours=8),
    )

    db.add(session_row)
    txn.is_used = True
    db.commit()

    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard",
        status_code=302,
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=getattr(settings, "APP_ENV", "development") == "production",
        samesite="lax",
        max_age=60 * 60 * 8,
    )

    return response  

async def get_me_module(
        session_token: str | None = Cookie(default=None),
        db: Session = None,
    ):
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_row = (
        db.query(UserSession)
        .filter(UserSession.session_token == session_token)
        .first()
    )

    if not session_row:
        raise HTTPException(status_code=401, detail="Invalid session")

    if session_row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Session expired")

    member = session_row.member

    return {
        "authenticated": True,
        "member": {
            "id": member.id,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "email": member.email,
            "upi": member.upi,
            "role": member.role,
        },
    }

async def get_logout_module(
        session_token: str | None = Cookie(default=None),
        db: Session = None,
    ):
    if session_token:
        session_row = (
            db.query(UserSession)
            .filter(UserSession.session_token == session_token)
            .first()
        )
        if session_row:
            db.delete(session_row)
            db.commit()

    response = JSONResponse({"ok": True})
    response.delete_cookie("session_token")
    return response   