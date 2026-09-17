from datetime import datetime, timedelta

from fastapi import HTTPException, Cookie
from fastapi.responses import RedirectResponse, JSONResponse

from sqlalchemy.orm import Session

import secrets
import hashlib
import base64
import urllib.parse
import httpx

from v1.oauth_transaction.model import OAuthTransaction
from v1.member.model import Member
from v1.user_session.model import UserSession
from v1.email.mailer import MailerConfigurationError, MailerDeliveryError, send_email
from v1.email_verification_token.model import EmailVerificationToken

from config.config_loader import settings

from v1.auth.service_extension import CurrentMember

EMAIL_TOKEN_MINUTES = 30
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

def extract_upi_from_email(email: str) -> str | None:
    if not email or "@" not in email:
        return None
    return email.split("@")[0].lower()

def generate_state() -> str:
    return secrets.token_urlsafe(32)

def generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)

def generate_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def normalize_auth_provider(provider: str | None = None) -> str:
    normalized = (provider or settings.AUTH_PROVIDER or "sso").strip().lower()
    if normalized not in {"sso", "google"}:
        return "sso"
    return normalized


def get_oauth_config(provider: str):
    if provider == "sso":
        return {
            "client_id": settings.SSO_OAUTH_CLIENT_ID or settings.OAUTH_CLIENT_ID,
            "client_secret": settings.SSO_OAUTH_CLIENT_SECRET or settings.OAUTH_CLIENT_SECRET,
            "authorize_url": settings.SSO_OAUTH_AUTHORIZE_URL or settings.OAUTH_AUTHORIZE_URL,
            "token_url": settings.SSO_OAUTH_TOKEN_URL or settings.OAUTH_TOKEN_URL,
            "userinfo_url": settings.SSO_OAUTH_USERINFO_URL or settings.OAUTH_USERINFO_URL,
            "redirect_uri": settings.SSO_OAUTH_REDIRECT_URI or settings.OAUTH_REDIRECT_URI,
            "scope": settings.SSO_OAUTH_SCOPE or f"openid profile {settings.OAUTH_EXTRA_SCOPE}".strip(),
        }

    return {
        "client_id": settings.OAUTH_CLIENT_ID,
        "client_secret": settings.OAUTH_CLIENT_SECRET,
        "authorize_url": settings.OAUTH_AUTHORIZE_URL,
        "token_url": settings.OAUTH_TOKEN_URL,
        "userinfo_url": GOOGLE_USERINFO_URL,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "scope": settings.OAUTH_SCOPE,
    }


def get_frontend_login_url(message: str | None = None) -> str:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    if not message:
        return frontend_url
    return f"{frontend_url}?message={urllib.parse.quote(message)}"


def create_session_response(
    db: Session,
    member: Member,
    access_token: str = "",
    refresh_token: str | None = None,
    id_token: str | None = None,
    token_type: str | None = None,
    scope: str | None = None,
):
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
    db.commit()

    dashboard_path = get_dashboard_path_for_role(member.role)

    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL.rstrip('/')}{dashboard_path}",
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


def get_member_by_email(db: Session, email: str) -> Member | None:
    return db.query(Member).filter(Member.email.ilike(email)).first()


def create_email_token(db: Session, member: Member, purpose: str) -> EmailVerificationToken:
    token_row = EmailVerificationToken(
        token=secrets.token_urlsafe(48),
        member_id=member.id,
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_MINUTES),
        is_used=False,
    )
    db.add(token_row)
    db.commit()
    db.refresh(token_row)
    return token_row


def send_auth_email(email: str, token: str, purpose: str) -> None:
    verify_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/api/v1/auth/email/verify"
        f"?token={urllib.parse.quote(token)}"
    )
    subject = "Verify your Marchir account" if purpose == "verify" else "Sign in to Marchir"

    if purpose == "verify":
        lead = "Please verify your email address before signing in."
        button = "Verify email"
    else:
        lead = "Use this secure link to sign in."
        button = "Sign in"

    text_body = f"{lead}\n\n{verify_url}\n\nThis link expires in {EMAIL_TOKEN_MINUTES} minutes."
    html_body = (
        f"<p>{lead}</p>"
        f'<p><a href="{verify_url}">{button}</a></p>'
        f"<p>This link expires in {EMAIL_TOKEN_MINUTES} minutes.</p>"
    )

    send_email(email, subject, text_body, html_body)


def mark_member_details(member: Member, userinfo: dict, provider: str) -> None:
    given_name = userinfo.get("given_name")
    family_name = userinfo.get("family_name")

    if not member.first_name and given_name:
        member.first_name = given_name

    if not member.last_name and family_name:
        member.last_name = family_name

    if not member.auth_provider:
        member.auth_provider = provider


async def get_auth_config_module():
    return {"auth_provider": normalize_auth_provider()}


async def get_login_module(db:Session, provider: str | None = None):
    auth_provider = normalize_auth_provider(provider)
    oauth_config = get_oauth_config(auth_provider)
    state = generate_state()
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    txn = OAuthTransaction(
        state=state,
        code_verifier=code_verifier,
        redirect_uri=oauth_config["redirect_uri"],
        provider=auth_provider,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        is_used=False,
    )
    db.add(txn)
    db.commit()

    params = {
        "response_type": "code",
        "client_id": oauth_config["client_id"],
        "redirect_uri": oauth_config["redirect_uri"],
        "scope": oauth_config["scope"],
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = oauth_config["authorize_url"] + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url, status_code=302)

def get_dashboard_path_for_role(role: str | None) -> str:
    normalized_role = (role or "").strip().lower()

    if normalized_role == "student":
        return "/student"
    if normalized_role == "teacher":
        return "/teacher"
    if normalized_role == "admin":
        return "/admin"

    return "/"

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

    auth_provider = normalize_auth_provider(getattr(txn, "provider", None))
    oauth_config = get_oauth_config(auth_provider)

    token_payload = {
        "grant_type": "authorization_code",
        "client_id": oauth_config["client_id"],
        "code": code,
        "redirect_uri": txn.redirect_uri,
        "code_verifier": txn.code_verifier,
    }

    if oauth_config["client_secret"]:
        token_payload["client_secret"] = oauth_config["client_secret"]

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_resp = await client.post(
            oauth_config["token_url"],
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
            oauth_config["userinfo_url"],
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

    if auth_provider == "sso":
        upi = userinfo.get("preferred_username")
        if upi:
            upi = upi.lower()
        else:
            upi = extract_upi_from_email(email)

        if not upi:
            raise HTTPException(status_code=403, detail="Could not determine UPI")

        member = (
            db.query(Member)
            .filter(Member.upi.isnot(None))
            .filter(Member.upi.ilike(upi))
            .first()
        )

        if not member:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. UPI '{upi}' is not registered.",
            )

        member.email_verified = True
        member.email_verified_at = member.email_verified_at or datetime.utcnow()
    else:
        member = get_member_by_email(db, email)
        if not member:
            member = Member(
                email=email.lower(),
                upi=extract_upi_from_email(email),
                role="student",
                auth_provider="google",
                email_verified=False,
            )
            db.add(member)
            db.commit()
            db.refresh(member)

        if not member.email_verified:
            mark_member_details(member, userinfo, "google")
            token_row = create_email_token(db, member, "verify")
            txn.is_used = True
            db.commit()
            try:
                send_auth_email(email, token_row.token, "verify")
            except MailerConfigurationError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
            except MailerDeliveryError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc

            return RedirectResponse(
                url=get_frontend_login_url(
                    "Account created. Please open your email to verify it, then return to login."
                ),
                status_code=302,
            )

    mark_member_details(member, userinfo, auth_provider)
    txn.is_used = True
    db.commit()

    return create_session_response(
        db,
        member,
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=id_token,
        token_type=token_type,
        scope=scope,
    )


async def post_email_login_module(db: Session, email: str):
    normalized_email = email.strip().lower()
    member = get_member_by_email(db, normalized_email)

    if not member:
        member = Member(
            email=normalized_email,
            upi=extract_upi_from_email(normalized_email),
            role="student",
            auth_provider="email",
            email_verified=False,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    purpose = "login" if member.email_verified else "verify"
    token_row = create_email_token(db, member, purpose)

    try:
        send_auth_email(normalized_email, token_row.token, purpose)
    except MailerConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except MailerDeliveryError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if purpose == "verify":
        message = "Account created. Please open your email to verify it, then return to login."
    else:
        message = "Please open your email and use the sign-in link to continue."

    return {"ok": True, "message": message}


async def get_email_verify_module(db: Session, token: str | None = None):
    if not token:
        raise HTTPException(status_code=400, detail="Missing verification token")

    token_row = (
        db.query(EmailVerificationToken)
        .filter(EmailVerificationToken.token == token)
        .first()
    )

    if not token_row or token_row.is_used or token_row.expires_at < datetime.utcnow():
        return RedirectResponse(
            url=get_frontend_login_url("This email link is invalid or has expired."),
            status_code=302,
        )

    member = db.query(Member).filter(Member.id == token_row.member_id).first()
    if not member:
        raise HTTPException(status_code=400, detail="Member not found")

    token_row.is_used = True
    token_row.used_at = datetime.utcnow()

    if token_row.purpose == "verify":
        member.email_verified = True
        member.email_verified_at = datetime.utcnow()
        db.commit()
        return RedirectResponse(
            url=get_frontend_login_url("Email verified. Please return to login."),
            status_code=302,
        )

    if not member.email_verified:
        member.email_verified = True
        member.email_verified_at = datetime.utcnow()

    return create_session_response(db, member)

async def get_me_module(
        member: CurrentMember
    ):
    return {
        "authenticated": True,
        "member": {
            "id": member.id,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "email": member.email,
            "upi": member.upi,
            "role": member.role,
            "email_verified": member.email_verified,
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
