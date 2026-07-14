"""HTTP-level tests for the job-match endpoints (DB-free via overrides)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints import job_match as jm_module
from app.core.config import settings
from app.main import app
from app.models.job_match import JobMatch
from app.models.user import User


def _make_match(resume_id) -> JobMatch:
    return JobMatch(
        id=uuid.uuid4(),
        resume_id=resume_id,
        job_title="Backend Engineer",
        job_description="Need Python and AWS.",
        match_score=50.0,
        matching_skills=["Python"],
        missing_skills=["AWS"],
        extra_skills=["React"],
        recommendations=["Add experience with: AWS."],
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client(fake_user: User):
    async def _override_user():
        return fake_user

    async def _override_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_active_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_match_endpoint(client: TestClient, fake_user: User) -> None:
    rid = uuid.uuid4()
    jm_module.create_job_match = AsyncMock(return_value=_make_match(rid))
    try:
        response = client.post(
            f"{settings.api_v1_prefix}/job-match",
            json={"resume_id": str(rid), "job_description": "Need Python and AWS."},
        )
    finally:
        from app.services import job_match_service

        jm_module.create_job_match = job_match_service.create_job_match
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["match_score"] == 50.0
    assert body["matching_skills"] == ["Python"]
    assert body["missing_skills"] == ["AWS"]


def test_create_match_rejects_invalid_resume_id(client: TestClient) -> None:
    response = client.post(
        f"{settings.api_v1_prefix}/job-match",
        json={"resume_id": "not-a-uuid", "job_description": "some job description text"},
    )
    assert response.status_code == 422


def test_list_matches_endpoint(client: TestClient, fake_user: User) -> None:
    rid = uuid.uuid4()
    jm_module.list_job_matches = AsyncMock(return_value=[_make_match(rid)])
    try:
        response = client.get(f"{settings.api_v1_prefix}/job-match/{rid}")
    finally:
        from app.services import job_match_service

        jm_module.list_job_matches = job_match_service.list_job_matches
    assert response.status_code == 200
    assert len(response.json()) == 1
