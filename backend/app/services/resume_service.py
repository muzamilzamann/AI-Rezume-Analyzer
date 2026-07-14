"""Resume business logic: validation, storage, parsing, and persistence."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ParsedResume
from app.services.parser import extract_text, parse_resume
from app.services.storage import StorageResult, delete_bytes, upload_bytes

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class ResumeError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _ext(filename: str) -> str:
    import os

    return os.path.splitext(filename or "")[1].lower()


def validate_upload(filename: str, content_type: str | None, size: int) -> None:
    ext = _ext(filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ResumeError(
            f"Unsupported file type '{ext or 'none'}'. Allowed: {allowed}.",
            status_code=415,
        )
    if size > MAX_FILE_BYTES:
        limit_mb = MAX_FILE_BYTES // (1024 * 1024)
        raise ResumeError(
            f"File too large ({size} bytes). Maximum allowed is {limit_mb} MB.",
            status_code=413,
        )
    if size == 0:
        raise ResumeError("Uploaded file is empty.", status_code=400)


async def create_resume(
    db: AsyncSession,
    user: User,
    data: bytes,
    filename: str,
    content_type: str | None,
) -> Resume:
    validate_upload(filename, content_type, len(data))

    storage: StorageResult = await upload_bytes(data, filename, content_type)

    raw_text = ""
    parsed = ParsedResume()
    try:
        raw_text = extract_text(data, content_type, filename)
        if raw_text:
            parsed = parse_resume(raw_text)
    except Exception:
        # Parsing must never break the upload; we keep raw_text/parsed empty.
        raw_text = raw_text or ""

    resume = Resume(
        user_id=user.id,
        file_url=storage.file_url,
        file_name=filename,
        storage_id=storage.storage_id,
        content_type=content_type,
        raw_text=raw_text or None,
        parsed_data=parsed.model_dump(),
    )
    db.add(resume)
    await db.flush()
    await db.refresh(resume)
    return resume


async def list_resumes(db: AsyncSession, user: User) -> list[Resume]:
    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.created_at.desc())
    )
    return list(result.scalars().all())


async def get_resume(db: AsyncSession, user: User, resume_id: uuid.UUID) -> Resume:
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise ResumeError("Resume not found.", status_code=404)
    return resume


async def delete_resume(db: AsyncSession, user: User, resume_id: uuid.UUID) -> None:
    resume = await get_resume(db, user, resume_id)
    storage_id = resume.storage_id
    # Determine backend from URL scheme: cloudinary URLs are https, local are host URLs.
    backend = "cloudinary" if resume.file_url.startswith("https://res.cloudinary.com") else "local"
    await db.delete(resume)
    await db.flush()
    if storage_id:
        await delete_bytes(storage_id, backend)


def parsed_resume_of(resume: Resume) -> ParsedResume:
    data: dict[str, Any] = resume.parsed_data or {}
    return ParsedResume.model_validate(data)
