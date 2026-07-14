"""HTTP-level tests for the admin endpoints (DB-free via overrides)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_current_superuser, get_db
from app.api.v1.endpoints import admin as admin_module
from app.core.config import settings
from app.main import app
from app.models.user import User
from app.schemas.admin import AdminStats, AdminUserRead


@pytest.fixture
def client(fake_user: User):
    async def _override_superuser():
        fake_user.is_superuser = True
        return fake_user

    async def _override_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_superuser] = _override_superuser
    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_admin_stats(client: TestClient) -> None:
    stats = AdminStats(
        total_users=5, active_users=4, total_resumes=12,
        total_analyses=8, total_job_matches=3, avg_ats_score=72.5,
    )
    admin_module.get_stats = AsyncMock(return_value=stats)
    try:
        response = client.get(f"{settings.api_v1_prefix}/admin/stats")
    finally:
        from app.services import admin_service

        admin_module.get_stats = admin_service.get_stats
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_users"] == 5
    assert body["avg_ats_score"] == 72.5


def test_admin_users_list(client: TestClient) -> None:
    users = [
        AdminUserRead(
            id="11111111-1111-1111-1111-111111111111",
            name="Alice", email="alice@x.com",
            is_active=True, is_superuser=False, created_at="2026-01-01T00:00:00",
            resume_count=3,
        )
    ]
    admin_module.list_users = AsyncMock(return_value=users)
    try:
        response = client.get(f"{settings.api_v1_prefix}/admin/users")
    finally:
        from app.services import admin_service

        admin_module.list_users = admin_service.list_users
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Alice"
    assert response.json()[0]["resume_count"] == 3


def test_non_superuser_blocked(fake_user: User) -> None:
    # Override the *active user* dep (not the superuser dep) so the real
    # get_current_superuser authorization check actually runs and rejects.
    async def _override_active():
        fake_user.is_superuser = False
        return fake_user

    async def _override_db():
        from unittest.mock import AsyncMock as _AM

        yield _AM()

    app.dependency_overrides[get_current_active_user] = _override_active
    app.dependency_overrides[get_db] = _override_db
    try:
        with TestClient(app) as c:
            response = c.get(f"{settings.api_v1_prefix}/admin/stats")
            assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
