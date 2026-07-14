"""Admin business logic: platform analytics and user management."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.user import User
from app.schemas.admin import AdminStats, AdminUserRead


class AdminError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


async def get_stats(db: AsyncSession) -> AdminStats:
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    active_users = (
        await db.execute(select(func.count(User.id)).where(User.is_active.is_(True)))
    ).scalar_one()
    total_resumes = (await db.execute(select(func.count(Resume.id)))).scalar_one()
    total_analyses = (await db.execute(select(func.count(Analysis.id)))).scalar_one()
    total_job_matches = (await db.execute(select(func.count(JobMatch.id)))).scalar_one()
    avg_ats = (
        await db.execute(select(func.avg(Resume.ats_score)).where(Resume.ats_score.is_not(None)))
    ).scalar_one()

    return AdminStats(
        total_users=total_users,
        active_users=active_users,
        total_resumes=total_resumes,
        total_analyses=total_analyses,
        total_job_matches=total_job_matches,
        avg_ats_score=round(float(avg_ats), 1) if avg_ats is not None else None,
    )


async def list_users(db: AsyncSession) -> list[AdminUserRead]:
    users = (await db.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
    counts_rows = (
        await db.execute(
            select(Resume.user_id, func.count(Resume.id)).group_by(Resume.user_id)
        )
    ).all()
    counts = {row[0]: row[1] for row in counts_rows}

    return [
        AdminUserRead(
            id=str(u.id),
            name=u.name,
            email=u.email,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            created_at=u.created_at.isoformat() if u.created_at else "",
            resume_count=counts.get(u.id, 0),
        )
        for u in users
    ]


async def set_user_active(
    db: AsyncSession, user_id: uuid.UUID, is_active: bool
) -> User:
    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if user is None:
        raise AdminError("User not found.", status_code=404)
    user.is_active = is_active
    await db.flush()
    await db.refresh(user)
    return user
