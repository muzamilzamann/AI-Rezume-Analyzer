"""Tests for the resume service layer."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.schemas.resume import ParsedResume
from app.services.resume_service import (
    MAX_FILE_BYTES,
    ResumeError,
    create_resume,
    parsed_resume_of,
    validate_upload,
)
from tests._helpers import build_docx

DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_validate_upload_rejects_bad_extension() -> None:
    with pytest.raises(ResumeError) as exc:
        validate_upload("file.txt", "text/plain", 100)
    assert exc.value.status_code == 415


def test_validate_upload_rejects_oversize() -> None:
    with pytest.raises(ResumeError) as exc:
        validate_upload("file.pdf", "application/pdf", MAX_FILE_BYTES + 1)
    assert exc.value.status_code == 413


def test_validate_upload_rejects_empty() -> None:
    with pytest.raises(ResumeError) as exc:
        validate_upload("file.pdf", "application/pdf", 0)
    assert exc.value.status_code == 400


def test_validate_upload_accepts_pdf_and_docx() -> None:
    validate_upload("a.pdf", "application/pdf", 1024)
    validate_upload("a.docx", DOCX_CT, 1024)


@pytest.mark.asyncio
async def test_create_resume_parses_and_persists(
    tmp_path, monkeypatch, fake_user, sample_resume_text
) -> None:
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "")
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "backend_base_url", "http://test.local")

    data = build_docx(sample_resume_text)
    db = AsyncMock()
    db.add = lambda obj: None  # add() is synchronous

    resume = await create_resume(db, fake_user, data, "jane-doe.docx", DOCX_CT)

    db.flush.assert_awaited_once()
    db.refresh.assert_awaited_once()
    assert resume.user_id == fake_user.id
    assert resume.file_name == "jane-doe.docx"
    assert resume.content_type and "wordprocessingml" in resume.content_type
    assert resume.raw_text and "Jane Doe" in resume.raw_text
    assert resume.parsed_data is not None
    assert resume.parsed_data["email"] == "jane.doe@email.com"
    assert "Python" in resume.parsed_data["skills"]


@pytest.mark.asyncio
async def test_create_resume_rejects_unsupported_type(fake_user) -> None:
    db = AsyncMock()
    with pytest.raises(ResumeError) as exc:
        await create_resume(db, fake_user, b"data", "file.txt", "text/plain")
    assert exc.value.status_code == 415
    db.flush.assert_not_called()


def test_parsed_resume_of_handles_missing_data(fake_user) -> None:
    from app.models.resume import Resume

    resume = Resume(
        user_id=fake_user.id,
        file_url="http://x/y.pdf",
        file_name="y.pdf",
    )
    resume.parsed_data = None
    parsed = parsed_resume_of(resume)
    assert isinstance(parsed, ParsedResume)
    assert parsed.skills == []
