"""Job-description matching endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DBSession, get_current_active_user
from app.models.job_match import JobMatch
from app.models.user import User
from app.schemas.job_match import JobMatchCreate, JobMatchRead
from app.services.job_match_service import (
    JobMatchError,
    create_job_match,
    delete_job_match,
    get_job_match,
    list_job_matches,
)

router = APIRouter(prefix="/job-match", tags=["job-match"])

CurrentUser = Annotated[User, Depends(get_current_active_user)]


def _to_read(jm: JobMatch) -> JobMatchRead:
    return JobMatchRead.model_validate(
        {
            "id": str(jm.id),
            "resume_id": str(jm.resume_id),
            "job_title": jm.job_title,
            "job_description": jm.job_description,
            "match_score": jm.match_score,
            "matching_skills": jm.matching_skills or [],
            "missing_skills": jm.missing_skills or [],
            "extra_skills": jm.extra_skills or [],
            "recommendations": jm.recommendations or [],
            "created_at": jm.created_at.isoformat() if jm.created_at else None,
        }
    )


@router.post("", response_model=JobMatchRead, status_code=201)
async def create_match(
    payload: JobMatchCreate, db: DBSession, current_user: CurrentUser
) -> JobMatchRead:
    try:
        resume_id = uuid.UUID(payload.resume_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid resume_id") from exc
    try:
        jm = await create_job_match(
            db, current_user, resume_id, payload.job_title, payload.job_description
        )
    except JobMatchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _to_read(jm)


# NOTE: /result/{match_id} must be declared before /{resume_id} so the literal
# "result" segment isn't captured by the {resume_id} path parameter.
@router.get("/result/{match_id}", response_model=JobMatchRead)
async def read_match(
    match_id: uuid.UUID, db: DBSession, current_user: CurrentUser
) -> JobMatchRead:
    try:
        jm = await get_job_match(db, current_user, match_id)
    except JobMatchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _to_read(jm)


@router.delete("/result/{match_id}", status_code=204)
async def remove_match(
    match_id: uuid.UUID, db: DBSession, current_user: CurrentUser
) -> None:
    try:
        await delete_job_match(db, current_user, match_id)
    except JobMatchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/{resume_id}", response_model=list[JobMatchRead])
async def list_matches(
    resume_id: uuid.UUID, db: DBSession, current_user: CurrentUser
) -> list[JobMatchRead]:
    try:
        matches = await list_job_matches(db, current_user, resume_id)
    except JobMatchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return [_to_read(m) for m in matches]
