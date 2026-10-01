from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from config.core import Base, get_db
from v1.auth.admin_session import AdminIdentity, get_current_admin
from v1.auth.controller import router as auth_router
from v1.auth.service import create_session_response
from v1.auth.messages import ACCOUNT_SUSPENDED_MESSAGE
from urllib.parse import parse_qs, urlparse
from v1.email_verification_token.model import EmailVerificationToken
from v1.enrollment.model import Enrollment
from v1.course.model import Course
from v1.course.teacher_assignment import TeacherCourseAssignment
from v1.marker_result.model import MarkerResult
from v1.marker_result.controller import router as marker_router
from v1.member.admin import router as users_router
from v1.member.model import Member
from v1.oauth_transaction.model import OAuthTransaction
from v1.user_session.model import UserSession


@pytest.fixture
def context():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    tables = [model.__table__ for model in (Member, Course, Enrollment, MarkerResult, UserSession, EmailVerificationToken, OAuthTransaction, TeacherCourseAssignment)]
    Base.metadata.create_all(engine, tables=tables)
    db = Session(engine, expire_on_commit=False)
    courses = [Course(name="Art", course_code="ART", is_active=True), Course(name="Biology", course_code="BIO", is_active=True), Course(name="Old", course_code="OLD", is_active=False)]
    users = [Member(first_name="Alice", last_name="Able", email="alice@example.com", upi="alice", role="student", email_verified=True), Member(first_name="Bob", last_name="Baker", email="bob@example.com", upi="bob", role="teacher", is_active=False), Member(first_name="Charlie", last_name="Cole", email="charlie@example.com", role="student")]
    db.add_all(courses + users)
    db.flush()
    enrollments = [Enrollment(member_id=users[0].id, course_id=courses[0].id), Enrollment(member_id=users[0].id, course_id=courses[2].id), Enrollment(member_id=users[1].id, course_id=courses[1].id)]
    db.add_all(enrollments)
    db.flush()
    db.add(MarkerResult(enrollment_id=enrollments[1].id, status="Submitted"))
    db.commit()
    app = FastAPI()
    app.include_router(users_router)
    app.include_router(auth_router)
    app.include_router(marker_router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_admin] = lambda: AdminIdentity(username="test-admin")
    with TestClient(app) as client:
        yield client, db, users, courses, enrollments
    db.close()
    engine.dispose()


def test_search_filters_sort_and_pagination(context):
    client, db, users, courses, enrollments = context
    result = client.get("/admin/users", params={"search": "alice able"}).json()
    assert [item["id"] for item in result["items"]] == [users[0].id]
    assert result["items"][0]["enrollments"][1]["has_submission"]
    assert client.get("/admin/users", params={"search": "%"}).json()["total"] == 0
    assert client.get("/admin/users", params={"role": "teacher", "active": "false"}).json()["total"] == 1
    assert {item["id"] for item in client.get("/admin/users", params={"unenrolled": "true"}).json()["items"]} == {users[1].id, users[2].id}
    assert client.get("/admin/users", params={"submission": "yes"}).json()["total"] == 1
    assert client.get("/admin/users", params={"course_id": courses[0].id, "submission": "no"}).json()["total"] == 1
    assert client.get("/admin/users", params={"course_id": courses[0].id, "submission": "yes"}).json()["total"] == 0
    result = client.get("/admin/users", params={"sort": "name", "direction": "desc", "page_size": 1, "page": 2}).json()
    assert result["total"] == 3
    assert result["items"][0]["id"] == users[1].id
    assert client.get("/admin/users", params={"sort": "course"}).status_code == 200


def test_move_only_unsubmitted_enrollment_and_keep_other_courses(context):
    client, db, users, courses, enrollments = context
    response = client.post(f"/admin/users/{users[0].id}/course", json={"enrollment_id": enrollments[0].id, "course_id": courses[1].id})
    assert response.status_code == 200
    db.refresh(enrollments[0]); db.refresh(enrollments[1])
    assert enrollments[0].course_id == courses[1].id
    assert enrollments[1].course_id == courses[2].id
    assert db.query(MarkerResult).count() == 1


def test_submitted_enrollment_cannot_be_moved(context):
    client, db, users, courses, enrollments = context
    response = client.post(f"/admin/users/{users[0].id}/course", json={"enrollment_id": enrollments[1].id, "course_id": courses[1].id})
    assert response.status_code == 409
    db.refresh(enrollments[1])
    assert enrollments[1].course_id == courses[2].id
    assert db.query(MarkerResult).count() == 1


def test_move_checks_ownership_and_active_destination(context):
    client, db, users, courses, enrollments = context
    assert client.post(f"/admin/users/{users[0].id}/course", json={"enrollment_id": enrollments[2].id, "course_id": courses[1].id}).status_code == 404
    assert client.post(f"/admin/users/{users[0].id}/course", json={"enrollment_id": enrollments[0].id, "course_id": courses[2].id}).status_code == 400
    assert client.post(f"/admin/users/{users[0].id}/course", json={"course_id": courses[0].id}).status_code == 409


def test_enroll_user_with_no_course(context):
    client, db, users, courses, enrollments = context
    assert client.post(f"/admin/users/{users[2].id}/course", json={"course_id": courses[1].id}).status_code == 200
    assert db.query(Enrollment).filter_by(member_id=users[2].id, course_id=courses[1].id).count() == 1


def test_deactivation_revokes_sessions_and_email_links(context):
    client, db, users, courses, enrollments = context
    db.add(UserSession(session_token="user-token", member_id=users[0].id, access_token="", expires_at=datetime.utcnow() + timedelta(hours=1)))
    db.add(EmailVerificationToken(token="email-token", member_id=users[0].id, purpose="login", expires_at=datetime.utcnow() + timedelta(hours=1)))
    db.commit()
    assert client.patch(f"/admin/users/{users[0].id}", json={"is_active": False}).status_code == 200
    assert db.query(UserSession).count() == 0
    assert db.query(EmailVerificationToken).first().is_used
    response = client.post("/auth/email/login", json={"email": "alice@example.com", "course_id": courses[0].id})
    assert response.status_code == 403
    assert response.json()["detail"] == ACCOUNT_SUSPENDED_MESSAGE
    with pytest.raises(HTTPException) as caught:
        create_session_response(db, users[0])
    assert caught.value.status_code == 403
    assert client.patch(f"/admin/users/{users[0].id}", json={"is_active": True}).status_code == 200
    assert users[0].is_active


def test_existing_session_and_unused_email_link_reject_disabled_user(context):
    client, db, users, courses, enrollments = context
    db.add(UserSession(session_token="disabled-token", member_id=users[1].id, access_token="", expires_at=datetime.utcnow() + timedelta(hours=1)))
    db.add(EmailVerificationToken(token="disabled-email", member_id=users[1].id, purpose="login", expires_at=datetime.utcnow() + timedelta(hours=1)))
    db.commit()
    client.cookies.set("session_token", "disabled-token")
    response = client.get("/auth/me")
    assert response.status_code == 403
    assert response.json()["detail"] == ACCOUNT_SUSPENDED_MESSAGE
    response = client.get("/auth/email/verify?token=disabled-email", follow_redirects=False)
    assert response.status_code == 302
    assert parse_qs(urlparse(response.headers["location"]).query)["message"] == [ACCOUNT_SUSPENDED_MESSAGE]


def test_edit_details_and_roles_with_duplicate_validation(context):
    client, db, users, courses, enrollments = context
    assert client.patch(f"/admin/users/{users[0].id}", json={"role": "teacher", "first_name": " Alicia "}).status_code == 200
    assert users[0].role == "teacher"
    assert users[0].first_name == "Alicia"
    assert client.patch(f"/admin/users/{users[0].id}", json={"role": "admin"}).status_code == 422
    assert client.patch(f"/admin/users/{users[0].id}", json={"role": None}).status_code == 422
    assert client.patch(f"/admin/users/{users[0].id}", json={"email": "bob@example.com"}).status_code == 409
    assert client.patch(f"/admin/users/{users[0].id}", json={"email": "NEW@example.com"}).status_code == 200
    assert users[0].email == "new@example.com"
    assert not users[0].email_verified


def test_user_management_requires_separate_admin_session(context):
    client, db, users, courses, enrollments = context
    del client.app.dependency_overrides[get_current_admin]
    client.cookies.set("session_token", "ordinary-user")
    assert client.get("/admin/users").status_code == 401
    assert client.patch(f"/admin/users/{users[0].id}", json={"is_active": False}).status_code == 401
    assert client.post(f"/admin/users/{users[0].id}/course", json={"course_id": courses[1].id}).status_code == 401


@pytest.mark.parametrize("provider", ["google", "sso"])
def test_disabled_users_cannot_login_through_oauth(context, monkeypatch, provider):
    from v1.auth import service

    client, db, users, courses, enrollments = context
    state = f"test-state.course-{courses[1].id}"
    db.add(OAuthTransaction(state=state, code_verifier="test-verifier", redirect_uri="https://test/callback", provider=provider, expires_at=datetime.utcnow() + timedelta(minutes=10), is_used=False))
    db.commit()

    class OAuthResponse:
        status_code = 200

        def __init__(self, body):
            self.body = body

        def json(self):
            return self.body

    class OAuthClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            return OAuthResponse({"access_token": "test-access-token"})

        async def get(self, *args, **kwargs):
            return OAuthResponse({"email": "bob@example.com", "preferred_username": "bob"})

    monkeypatch.setattr(service.httpx, "AsyncClient", OAuthClient)
    response = client.get("/auth/callback", params={"state": state, "code": "test-code"}, follow_redirects=False)
    assert response.status_code == 302
    assert parse_qs(urlparse(response.headers["location"]).query)["message"] == [ACCOUNT_SUSPENDED_MESSAGE]
    assert db.query(UserSession).count() == 0


def test_role_changes_revoke_existing_sessions(context):
    client, db, users, courses, enrollments = context
    db.add(UserSession(session_token="old-role", member_id=users[0].id, access_token="", expires_at=datetime.utcnow() + timedelta(hours=1)))
    db.commit()
    assert client.patch(f"/admin/users/{users[0].id}", json={"role": "teacher"}).status_code == 200
    assert db.query(UserSession).count() == 0


def teacher_session(context):
    client, db, users, courses, enrollments = context
    users[1].is_active = True
    db.add(UserSession(session_token="teacher-token", member_id=users[1].id, access_token="", expires_at=datetime.utcnow() + timedelta(hours=1)))
    db.commit()
    client.cookies.set("session_token", "teacher-token")
    return users[1]


def test_teacher_assignments_support_multiple_courses_and_admin_filters(context):
    client, db, users, courses, enrollments = context
    response = client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[0].id, courses[1].id, courses[0].id]})
    assert response.status_code == 200
    assert db.query(TeacherCourseAssignment).count() == 2
    result = client.get("/admin/users", params={"role": "teacher", "course_id": courses[0].id}).json()
    assert result["total"] == 1
    assert {course["id"] for course in result["items"][0]["teacher_courses"]} == {courses[0].id, courses[1].id}
    assert client.get("/admin/users", params={"role": "teacher", "unenrolled": True}).json()["total"] == 0
    assert client.get("/admin/users", params={"sort": "course"}).status_code == 200


def test_teacher_cannot_gain_access_from_student_enrollment(context):
    client, db, users, courses, enrollments = context
    teacher_session(context)
    result = client.get("/marker-result-route/get-last-submission/active-with-students-and-submissions")
    assert result.status_code == 200
    assert result.json() == {"courses": []}
    assert client.get(f"/marker-result-route/download-marker-results-csv/{courses[1].id}").status_code == 403
    assert client.post("/marker-result-route/download-zip-course", data={"course_id": courses[1].id}).status_code == 403


def test_teacher_sees_only_assigned_courses_and_students(context):
    client, db, users, courses, enrollments = context
    teacher_session(context)
    client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[0].id, courses[1].id]})
    result = client.get("/marker-result-route/get-last-submission/active-with-students-and-submissions").json()
    assert {course["id"] for course in result["courses"]} == {courses[0].id, courses[1].id}
    assert result["courses"][0]["students"][0]["member_id"] == users[0].id
    assert result["courses"][1]["students"] == []
    assert client.get(f"/marker-result-route/download-marker-results-csv/{courses[0].id}").status_code == 200
    assert client.get(f"/marker-result-route/download-marker-results-csv/{courses[2].id}").status_code == 403
    client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[1].id]})
    assert client.get(f"/marker-result-route/download-marker-results-csv/{courses[0].id}").status_code == 403


def test_teacher_assignment_validation_and_role_demotion(context):
    client, db, users, courses, enrollments = context
    assert client.put(f"/admin/users/{users[0].id}/teacher-courses", json={"course_ids": [courses[0].id]}).status_code == 400
    assert client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [9999]}).status_code == 400
    assert client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[2].id]}).status_code == 400
    assert client.post(f"/admin/users/{users[1].id}/course", json={"course_id": courses[0].id}).status_code == 400
    assert client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[0].id]}).status_code == 200
    assert client.patch(f"/admin/users/{users[1].id}", json={"role": "student"}).status_code == 200
    assert db.query(TeacherCourseAssignment).count() == 0


def test_teacher_zip_authorization_and_path_safety(context, monkeypatch, tmp_path):
    from v1.marker_result import service
    import io
    import zipfile

    client, db, users, courses, enrollments = context
    teacher_session(context)
    monkeypatch.setattr(service, "COURSE_UPLOAD_ROOT", tmp_path)
    (tmp_path / "Art").mkdir()
    (tmp_path / "Art" / "student.zip").write_bytes(b"submission")
    client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[0].id]})
    result = client.post("/marker-result-route/download-zip-course", data={"course_id": courses[0].id})
    assert result.status_code == 200
    with zipfile.ZipFile(io.BytesIO(result.content)) as archive:
        assert archive.read("student.zip") == b"submission"
    courses[0].name = "../outside"
    db.commit()
    assert client.post("/marker-result-route/download-zip-course", data={"course_id": courses[0].id}).status_code == 400
    assert client.post("/marker-result-route/download-zip-course", data={"course": "../outside"}).status_code == 422


def test_regular_user_cannot_assign_teachers(context):
    client, db, users, courses, enrollments = context
    teacher_session(context)
    del client.app.dependency_overrides[get_current_admin]
    assert client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[0].id]}).status_code == 401


def test_teachers_do_not_share_each_others_course_access(context):
    client, db, users, courses, enrollments = context
    teacher_session(context)
    users[2].role = "teacher"
    db.commit()
    assert client.put(f"/admin/users/{users[2].id}/teacher-courses", json={"course_ids": [courses[0].id]}).status_code == 200
    assert client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": [courses[1].id]}).status_code == 200
    result = client.get("/marker-result-route/get-last-submission/active-with-students-and-submissions").json()
    assert [course["id"] for course in result["courses"]] == [courses[1].id]
    assert client.get(f"/marker-result-route/download-marker-results-csv/{courses[0].id}").status_code == 403
    assert client.put(f"/admin/users/{users[1].id}/teacher-courses", json={"course_ids": []}).status_code == 200
    assert client.get("/marker-result-route/get-last-submission/active-with-students-and-submissions").json() == {"courses": []}
