"""Analysis endpoints (ATS scoring + AI feedback)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import DBSession, get_current_active_user
from app.models.analysis import Analysis
from app.models.user import User
from app.schemas.analysis import AnalysisRead, AnalysisRunResponse
from app.services.analysis_service import (
    AnalysisError,
    get_analysis,
    run_ai_feedback,
    run_ats_analysis,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])

CurrentUser = Annotated[User, Depends(get_current_active_user)]


class RunRequest(BaseModel):
    resume_id: uuid.UUID


def _to_analysis_read(analysis: Analysis) -> AnalysisRead:
    return AnalysisRead.model_validate(
        {
            "id": str(analysis.id),
            "resume_id": str(analysis.resume_id),
            "overall_score": analysis.overall_score,
            "subscores": analysis.subscores,
            "strengths": analysis.strengths or [],
            "weaknesses": analysis.weaknesses or [],
            "recommendations": analysis.recommendations or [],
            "source": analysis.source,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        }
    )


@router.post("/run", response_model=AnalysisRunResponse)
async def run_analysis(
    payload: RunRequest, db: DBSession, current_user: CurrentUser
) -> AnalysisRunResponse:
    try:
        analysis, result = await run_ats_analysis(db, current_user, payload.resume_id)
    except AnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return AnalysisRunResponse(
        analysis=_to_analysis_read(analysis), resume_ats_score=result.overall_score
    )


@router.get("/{resume_id}", response_model=AnalysisRead)
async def read_analysis(
    resume_id: uuid.UUID, db: DBSession, current_user: CurrentUser
) -> AnalysisRead:
    try:
        analysis = await get_analysis(db, current_user, resume_id)
    except AnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _to_analysis_read(analysis)


@router.post("/ai-feedback", response_model=AnalysisRunResponse)
async def ai_feedback(
    payload: RunRequest, db: DBSession, current_user: CurrentUser
) -> AnalysisRunResponse:
    try:
        analysis, _ = await run_ai_feedback(db, current_user, payload.resume_id)
    except AnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return AnalysisRunResponse(
        analysis=_to_analysis_read(analysis),
        resume_ats_score=analysis.overall_score or 0.0,
    )
