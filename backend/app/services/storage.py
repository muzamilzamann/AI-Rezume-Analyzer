"""File storage abstraction.

Uploads to Cloudinary when credentials are configured, otherwise falls back to
the local filesystem (served via the mounted ``/uploads`` static route). This
keeps the upload flow fully functional in local development without requiring a
Cloudinary account.
"""

from __future__ import annotations

import asyncio
import contextlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


@dataclass(slots=True)
class StorageResult:
    file_url: str
    storage_id: str
    backend: str  # "cloudinary" | "local"


def is_cloudinary_configured() -> bool:
    return bool(
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    )


def _ext_for(content_type: str | None, filename: str) -> str:
    if filename and "." in filename:
        return Path(filename).suffix.lower()
    mapping = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }
    return mapping.get(content_type or "", "")


def _safe_local_name(filename: str) -> str:
    stem = Path(filename).stem or "resume"
    # keep it filesystem-safe
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)[:40]
    return f"{safe}_{uuid.uuid4().hex[:8]}"


def _local_upload_root() -> Path:
    root = Path(settings.local_upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _upload_to_cloudinary(
    data: bytes, filename: str, content_type: str | None
) -> StorageResult:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    public_id = f"resumes/{uuid.uuid4().hex}"
    resource = cloudinary.uploader.upload(
        data,
        public_id=public_id,
        resource_type="auto",
        overwrite=False,
        filename=filename,
    )
    return StorageResult(
        file_url=resource.get("secure_url", ""),
        storage_id=public_id,
        backend="cloudinary",
    )


def _upload_to_local(
    data: bytes, filename: str, content_type: str | None
) -> StorageResult:
    ext = _ext_for(content_type, filename)
    name = f"{_safe_local_name(filename)}{ext}"
    root = _local_upload_root()
    (root / name).write_bytes(data)
    base = settings.backend_base_url.rstrip("/")
    return StorageResult(
        file_url=f"{base}/{settings.local_upload_url}/{name}",
        storage_id=name,
        backend="local",
    )


async def upload_bytes(
    data: bytes, filename: str, content_type: str | None
) -> StorageResult:
    """Upload file bytes and return a URL + storage id. Runs in a worker thread."""
    func = _upload_to_cloudinary if is_cloudinary_configured() else _upload_to_local
    return await asyncio.to_thread(func, data, filename, content_type)


async def delete_bytes(storage_id: str, backend: str) -> None:
    """Best-effort deletion of a previously uploaded asset."""

    def _delete() -> None:
        if backend == "cloudinary" and is_cloudinary_configured():
            import cloudinary
            import cloudinary.uploader

            cloudinary.config(
                cloud_name=settings.cloudinary_cloud_name,
                api_key=settings.cloudinary_api_key,
                api_secret=settings.cloudinary_api_secret,
                secure=True,
            )
            with contextlib.suppress(Exception):
                cloudinary.uploader.destroy(storage_id, resource_type="auto")
        elif backend == "local":
            target = _local_upload_root() / storage_id
            if target.exists():
                target.unlink(missing_ok=True)

    await asyncio.to_thread(_delete)
