"""Job-description matching business logic."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_match import JobMatch
from app.models.user import User
from app.schemas.job_match import JobMatchResult
from app.services.parser import detect_skills
from app.services.resume_service import ResumeError, get_resume


class JobMatchError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def compute_match(resume_skills: list[str], job_description: str) -> JobMatchResult:
    jd_skills = detect_skills(job_description)
    resume_set = {s.lower() for s in resume_skills}

    matching: list[str] = []
    missing: list[str] = []
    seen: set[str] = set()
    for skill in jd_skills:
        key = skill.lower()
        if key in seen:
            continue
        seen.add(key)
        if key in resume_set:
            matching.append(skill)
        else:
            missing.append(skill)

    extra = [s for s in resume_skills if s.lower() not in {x.lower() for x in jd_skills}]

    score = 0.0 if not jd_skills else round((len(matching) / len(jd_skills)) * 100, 1)

    recommendations: list[str] = []
    if missing:
        top = missing[:5]
        recommendations.append(
            f"Add experience with: {', '.join(top)} — these appear in the job description."
        )
    if score >= 80:
        recommendations.append(
            "Strong match. Tailor your bullet points to mirror the JD language."
        )
    elif score >= 50:
        recommendations.append(
            "Partial match. Emphasize the matching skills and learn the missing ones."
        )
    else:
        recommendations.append(
            "Low skill overlap. Consider upskilling in the missing areas before applying."
        )
    if not resume_skills:
        recommendations.append(
            "Your resume has no detected skills — upload a parsed resume first."
        )

    return JobMatchResult(
        match_score=score,
        matching_skills=matching,
        missing_skills=missing,
        extra_skills=extra,
        recommendations=recommendations,
    )


async def create_job_match(
    db: AsyncSession,
    user: User,
    resume_id: uuid.UUID,
    job_title: str | None,
    job_description: str,
) -> JobMatch:
    try:
        resume = await get_resume(db, user, resume_id)
    except ResumeError as exc:
        raise JobMatchError(exc.detail, exc.status_code) from exc

    resume_skills = (resume.parsed_data or {}).get("skills") or []
    result = compute_match(resume_skills, job_description)

    job_match = JobMatch(
        resume_id=resume.id,
        job_title=job_title,
        job_description=job_description,
        match_score=result.match_score,
        matching_skills=result.matching_skills,
        missing_skills=result.missing_skills,
        extra_skills=result.extra_skills,
        recommendations=result.recommendations,
    )
    db.add(job_match)
    await db.flush()
    await db.refresh(job_match)
    return job_match


async def list_job_matches(
    db: AsyncSession, user: User, resume_id: uuid.UUID
) -> list[JobMatch]:
    try:
        await get_resume(db, user, resume_id)
    except ResumeError as exc:
        raise JobMatchError(exc.detail, exc.status_code) from exc
    result = await db.execute(
        select(JobMatch)
        .where(JobMatch.resume_id == resume_id)
        .order_by(JobMatch.created_at.desc())
    )
    return list(result.scalars().all())


async def get_job_match(
    db: AsyncSession, user: User, match_id: uuid.UUID
) -> JobMatch:
    result = await db.execute(select(JobMatch).where(JobMatch.id == match_id))
    job_match = result.scalar_one_or_none()
    if job_match is None:
        raise JobMatchError("Job match not found.", status_code=404)
    # Ensure ownership via the resume.
    try:
        await get_resume(db, user, job_match.resume_id)
    except ResumeError as exc:
        raise JobMatchError(exc.detail, exc.status_code) from exc
    return job_match


async def delete_job_match(db: AsyncSession, user: User, match_id: uuid.UUID) -> None:
    job_match = await get_job_match(db, user, match_id)
    await db.delete(job_match)
    await db.flush()
