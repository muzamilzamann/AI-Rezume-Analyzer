"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DBSession, get_current_active_user
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.schemas.common import Message
from app.services.auth_service import (
    AuthError,
    authenticate_user,
    issue_access_token,
    register_user,
    request_password_reset,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_read(user: User) -> UserRead:
    return UserRead.model_validate(
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(payload: UserCreate, db: DBSession) -> UserRead:
    try:
        user = await register_user(db, payload)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _to_user_read(user)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: DBSession) -> Token:
    try:
        user = await authenticate_user(db, payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    token = await issue_access_token(user)
    return Token(access_token=token, expires_in=settings.access_token_expire_minutes * 60)


@router.get("/me", response_model=UserRead)
async def read_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserRead:
    return _to_user_read(current_user)


@router.post("/forgot-password", response_model=Message)
async def forgot_password(payload: ForgotPasswordRequest, db: DBSession) -> Message:
    await request_password_reset(db, payload.email)
    return Message(message="If that email exists, a reset link has been generated.")


@router.post("/reset-password", response_model=Message)
async def reset_password_endpoint(
    payload: ResetPasswordRequest, db: DBSession
) -> Message:
    try:
        await reset_password(db, payload.token, payload.new_password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return Message(message="Password has been reset successfully.")
