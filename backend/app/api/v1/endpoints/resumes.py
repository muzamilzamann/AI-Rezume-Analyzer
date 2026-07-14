"""Resume upload and management endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import DBSession, get_current_active_user
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ParsedResume, ResumeRead, ResumeSummary, ResumeUploadResponse
from app.services.resume_service import (
    ResumeError,
    create_resume,
    delete_resume,
    get_resume,
    list_resumes,
    parsed_resume_of,
)

router = APIRouter(prefix="/resume", tags=["resume"])

CurrentUser = Annotated[User, Depends(get_current_active_user)]


def _to_resume_read(resume: Resume) -> ResumeRead:
    return ResumeRead.model_validate(
        {
            "id": str(resume.id),
            "user_id": str(resume.user_id),
            "file_url": resume.file_url,
            "file_name": resume.file_name,
            "content_type": resume.content_type,
            "ats_score": resume.ats_score,
            "raw_text": resume.raw_text,
            "parsed_data": resume.parsed_data,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
        }
    )


def _to_resume_summary(resume: Resume) -> ResumeSummary:
    skills = (resume.parsed_data or {}).get("skills", []) or []
    return ResumeSummary.model_validate(
        {
            "id": str(resume.id),
            "file_name": resume.file_name,
            "ats_score": resume.ats_score,
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
            "skills": skills,
        }
    )


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume(
    db: DBSession,
    current_user: CurrentUser,
    file: Annotated[UploadFile, File(description="PDF or DOCX resume (max 5 MB)")],
) -> ResumeUploadResponse:
    data = await file.read()
    filename = file.filename or "resume"
    try:
        resume = await create_resume(db, current_user, data, filename, file.content_type)
    except ResumeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return ResumeUploadResponse(resume=_to_resume_read(resume), parsed=parsed_resume_of(resume))


@router.get("", response_model=list[ResumeSummary])
async def list_my_resumes(db: DBSession, current_user: CurrentUser) -> list[ResumeSummary]:
    resumes = await list_resumes(db, current_user)
    return [_to_resume_summary(r) for r in resumes]


@router.get("/{resume_id}", response_model=ResumeRead)
async def read_resume(
    resume_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> ResumeRead:
    try:
        resume = await get_resume(db, current_user, resume_id)
    except ResumeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _to_resume_read(resume)


@router.get("/{resume_id}/parsed", response_model=ParsedResume)
async def read_parsed_resume(
    resume_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> ParsedResume:
    try:
        resume = await get_resume(db, current_user, resume_id)
    except ResumeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return parsed_resume_of(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_resume(
    resume_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    try:
        await delete_resume(db, current_user, resume_id)
    except ResumeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


class ParseStatus(BaseModel):
    resume_id: str
    parsed: bool
    skills_count: int


@router.get("/{resume_id}/status", response_model=ParseStatus)
async def parse_status(
    resume_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> ParseStatus:
    try:
        resume = await get_resume(db, current_user, resume_id)
    except ResumeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    parsed = parsed_resume_of(resume)
    return ParseStatus(
        resume_id=str(resume.id),
        parsed=bool(resume.parsed_data),
        skills_count=len(parsed.skills),
    )
