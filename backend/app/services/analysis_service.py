"""Analysis business logic: run ATS scoring and persist results."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.models.resume import Resume
from app.models.user import User
from app.schemas.analysis import AIFeedback, ATSResult
from app.services.ai_service import generate_feedback
from app.services.ats_service import compute_ats
from app.services.resume_service import ResumeError, get_resume


class AnalysisError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


async def _fetch_resume(db: AsyncSession, user: User, resume_id: uuid.UUID) -> Resume:
    try:
        return await get_resume(db, user, resume_id)
    except ResumeError as exc:
        raise AnalysisError(exc.detail, exc.status_code) from exc


async def get_analysis(db: AsyncSession, user: User, resume_id: uuid.UUID) -> Analysis:
    await _fetch_resume(db, user, resume_id)
    result = await db.execute(
        select(Analysis).where(Analysis.resume_id == resume_id)
    )
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise AnalysisError("No analysis found. Run an analysis first.", status_code=404)
    return analysis


async def run_ats_analysis(
    db: AsyncSession, user: User, resume_id: uuid.UUID
) -> tuple[Analysis, ATSResult]:
    resume = await _fetch_resume(db, user, resume_id)
    if not resume.raw_text:
        raise AnalysisError(
            "This resume has no extractable text, so ATS scoring is not possible.",
            status_code=422,
        )

    result = compute_ats(resume.raw_text, resume.parsed_data)

    existing = await db.execute(select(Analysis).where(Analysis.resume_id == resume_id))
    analysis = existing.scalar_one_or_none()

    if analysis is None:
        analysis = Analysis(resume_id=resume.id)
        db.add(analysis)

    analysis.overall_score = result.overall_score
    analysis.subscores = result.subscores.model_dump()
    analysis.strengths = result.strengths
    analysis.weaknesses = result.weaknesses
    analysis.recommendations = result.recommendations
    analysis.source = "ats"

    resume.ats_score = result.overall_score

    await db.flush()
    await db.refresh(analysis)
    return analysis, result


async def run_ai_feedback(
    db: AsyncSession, user: User, resume_id: uuid.UUID
) -> tuple[Analysis, AIFeedback]:
    """Generate AI (or rule-based) narrative feedback and attach it to the analysis."""
    resume = await _fetch_resume(db, user, resume_id)
    if not resume.raw_text:
        raise AnalysisError(
            "This resume has no extractable text, so feedback cannot be generated.",
            status_code=422,
        )

    # Ensure an ATS analysis exists (cheap; keeps subscores/overall fresh).
    analysis, ats_result = await run_ats_analysis(db, user, resume_id)

    feedback = generate_feedback(resume.raw_text, resume.parsed_data, ats_result)
    analysis.strengths = feedback.strengths
    analysis.weaknesses = feedback.weaknesses
    analysis.recommendations = feedback.recommendations
    analysis.source = feedback.source

    await db.flush()
    await db.refresh(analysis)
    return analysis, feedback
