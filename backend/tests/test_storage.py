"""Tests for the storage service (local fallback)."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.services.storage import delete_bytes, is_cloudinary_configured, upload_bytes


@pytest.mark.asyncio
async def test_local_upload_writes_file_and_returns_url(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "")
    monkeypatch.setattr(settings, "cloudinary_api_key", "")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "")
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "backend_base_url", "http://test.local")

    assert is_cloudinary_configured() is False

    result = await upload_bytes(b"%PDF-1.4 fake", "my cv.pdf", "application/pdf")

    assert result.backend == "local"
    assert result.file_url.startswith("http://test.local/uploads/")
    assert result.file_url.endswith(".pdf")
    assert result.storage_id.endswith(".pdf")
    # File actually written to disk.
    files = list((tmp_path / "uploads").iterdir())
    assert len(files) == 1
    assert files[0].read_bytes() == b"%PDF-1.4 fake"

    # Deletion removes it.
    await delete_bytes(result.storage_id, "local")
    assert list((tmp_path / "uploads").iterdir()) == []


@pytest.mark.asyncio
async def test_delete_unknown_local_file_is_safe(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "local_upload_dir", str(tmp_path / "uploads"))
    await delete_bytes("does-not-exist.pdf", "local")  # should not raise
