"""HTTP-level tests for the resume endpoints (DB-free via dependency overrides)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints import resumes as resumes_module
from app.core.config import settings
from app.main import app
from app.models.resume import Resume
from app.models.user import User
from tests._helpers import build_docx

DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _make_resume(user: User) -> Resume:
    return Resume(
        id=uuid.uuid4(),
        user_id=user.id,
        file_url="http://test.local/uploads/jane.docx",
        file_name="jane.docx",
        storage_id="jane.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ats_score=None,
        raw_text="Jane Doe...",
        parsed_data={
            "name": "Jane Doe",
            "email": "jane.doe@email.com",
            "phone": None,
            "skills": ["Python", "FastAPI"],
            "education": [],
            "experience": [],
            "projects": [],
            "links": [],
            "word_count": 2,
        },
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


def test_upload_resume_returns_parsed(
    client: TestClient, fake_user: User, sample_resume_text: str
) -> None:
    data = build_docx(sample_resume_text)
    resumes_module.create_resume = AsyncMock(return_value=_make_resume(fake_user))
    try:
        response = client.post(
            f"{settings.api_v1_prefix}/resume/upload",
            files={"file": ("jane.docx", data, DOCX_CT)},
        )
    finally:
        # Restore the real function reference for other tests.
        from app.services import resume_service

        resumes_module.create_resume = resume_service.create_resume

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["resume"]["file_name"] == "jane.docx"
    assert body["resume"]["parsed_data"]["email"] == "jane.doe@email.com"
    assert body["parsed"]["skills"] == ["Python", "FastAPI"]
    assert body["resume"]["created_at"]


def test_upload_rejects_unsupported_type(client: TestClient) -> None:
    response = client.post(
        f"{settings.api_v1_prefix}/resume/upload",
        files={"file": ("notepad.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_get_resume_uses_owner_scope(client: TestClient, fake_user: User) -> None:
    fake = _make_resume(fake_user)
    resumes_module.get_resume = AsyncMock(return_value=fake)
    try:
        response = client.get(f"{settings.api_v1_prefix}/resume/{fake.id}")
    finally:
        from app.services import resume_service

        resumes_module.get_resume = resume_service.get_resume
    assert response.status_code == 200
    assert response.json()["id"] == str(fake.id)
