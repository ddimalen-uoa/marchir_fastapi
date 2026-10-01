from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config.config_loader import settings
from config.core import get_db
from rate_limiting import limiter
from v1.auth.admin_session import ADMIN_COOKIE, admin_session_key, create_admin_token
from v1.auth.controller import router as auth_router
from v1.course.controller import router as course_router
from v1.enrollment.controller import router as enrollment_router


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_USERNAME", "test-admin")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "test-password")
    monkeypatch.setattr(settings, "SESSION_SECRET", "test-session-secret")
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(limiter, "enabled", False)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(auth_router)
    app.include_router(course_router)
    app.include_router(enrollment_router)

    def no_database():
        raise AssertionError("Admin authentication must not access the database")

    app.dependency_overrides[get_db] = no_database
    with TestClient(app) as test_client:
        yield test_client


def sign_in(client):
    return client.post("/auth/admin/login", json={"username": "test-admin", "password": "test-password"})


def test_admin_login_and_logout_without_member_record(client):
    assert client.get("/auth/admin/me").status_code == 401
    response = sign_in(client)
    assert response.status_code == 200
    assert response.json()["admin"] == {"username": "test-admin", "role": "admin"}
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    assert client.get("/auth/admin/me").status_code == 200
    assert client.post("/auth/admin/logout").status_code == 200
    assert client.get("/auth/admin/me").status_code == 401


@pytest.mark.parametrize("username,password", [("wrong", "test-password"), ("test-admin", "wrong")])
def test_invalid_credentials(client, username, password):
    response = client.post("/auth/admin/login", json={"username": username, "password": password})
    assert response.status_code == 401
    assert ADMIN_COOKIE not in client.cookies


def test_unconfigured_admin_is_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "")
    assert sign_in(client).status_code == 503
    assert client.get("/auth/admin/me").status_code == 401


def test_expired_tampered_and_rotated_sessions(client, monkeypatch):
    expired = jwt.encode(
        {"sub": "test-admin", "aud": "marchir-admin", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        admin_session_key(), algorithm="HS256",
    )
    for token in (expired, create_admin_token() + "tampered"):
        client.cookies.set(ADMIN_COOKIE, token)
        assert client.get("/auth/admin/me").status_code == 401
    client.cookies.set(ADMIN_COOKIE, create_admin_token())
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "new-password")
    assert client.get("/auth/admin/me").status_code == 401


def test_unsigned_token_is_rejected(client):
    client.cookies.set(ADMIN_COOKIE, "eyJhbGciOiJub25lIn0.eyJzdWIiOiJ0ZXN0LWFkbWluIn0.")
    assert client.get("/auth/admin/me").status_code == 401


@pytest.mark.parametrize("method,path", [
    ("get", "/enrollment-route/get-courses-and-enrollment"),
    ("get", "/enrollment-route/auto-enroll"),
    ("post", "/course-route/add-course"),
    ("put", "/course-route/edit-course/1"),
])
def test_regular_user_cookie_cannot_access_admin_apis(client, method, path):
    client.cookies.set("session_token", "regular-user-session")
    assert getattr(client, method)(path).status_code == 401


def test_production_cookie_is_secure(client, monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    assert "Secure" in sign_in(client).headers["set-cookie"]


def test_admin_can_access_protected_course_api(client, monkeypatch):
    from v1.enrollment import service

    async def courses(admin, db):
        assert admin.username == "test-admin"
        assert admin.role == "admin"
        return []

    monkeypatch.setattr(service, "get_courses_and_enrollment", courses)
    client.app.dependency_overrides[get_db] = lambda: None
    assert sign_in(client).status_code == 200
    response = client.get("/enrollment-route/get-courses-and-enrollment")
    assert response.status_code == 200
    assert response.json() == []


def test_login_attempts_are_limited(client, monkeypatch):
    monkeypatch.setattr(limiter, "enabled", True)
    limiter.reset()
    for _ in range(5):
        assert sign_in(client).status_code == 200
    assert sign_in(client).status_code == 429
    limiter.reset()
