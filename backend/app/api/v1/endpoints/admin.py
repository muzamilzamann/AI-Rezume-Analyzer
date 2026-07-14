"""Admin endpoints (superuser only)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import DBSession, get_current_superuser
from app.models.user import User
from app.schemas.admin import AdminStats, AdminUserRead, UserActiveUpdate
from app.services.admin_service import AdminError, get_stats, list_users, set_user_active

router = APIRouter(prefix="/admin", tags=["admin"])

SuperUser = Annotated[User, Depends(get_current_superuser)]


@router.get("/stats", response_model=AdminStats)
async def stats(db: DBSession, _: SuperUser) -> AdminStats:
    return await get_stats(db)


@router.get("/users", response_model=list[AdminUserRead])
async def users(db: DBSession, _: SuperUser) -> list[AdminUserRead]:
    return await list_users(db)


@router.patch("/users/{user_id}", response_model=AdminUserRead)
async def update_user_active(
    user_id: uuid.UUID,
    payload: UserActiveUpdate,
    db: DBSession,
    current: SuperUser,
) -> AdminUserRead:
    try:
        user = await set_user_active(db, user_id, payload.is_active)
    except AdminError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return AdminUserRead(
        id=str(user.id),
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at.isoformat() if user.created_at else "",
        resume_count=0,
    )
