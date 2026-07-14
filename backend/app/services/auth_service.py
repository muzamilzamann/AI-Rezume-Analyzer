"""Authentication business logic."""

from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserCreate


class AuthError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, payload: UserCreate) -> User:
    existing = await get_user_by_email(db, payload.email)
    if existing is not None:
        raise AuthError("An account with this email already exists.", status_code=409)

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email.lower())
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("Invalid email or password.", status_code=401)
    if not user.is_active:
        raise AuthError("This account has been deactivated.", status_code=403)
    return user


async def issue_access_token(user: User) -> str:
    return create_access_token(subject=str(user.id))


async def request_password_reset(db: AsyncSession, email: str) -> tuple[User, str]:
    """Return the reset token. In production this would be emailed; we return it for dev."""
    user = await get_user_by_email(db, email)
    if user is None:
        # Avoid user enumeration: return silently
        raise AuthError("If that email exists, a reset link has been generated.", status_code=200)
    token = create_password_reset_token(user.email)
    return user, token


async def reset_password(db: AsyncSession, token: str, new_password: str) -> User:
    try:
        payload = decode_token(token)
    except InvalidTokenError as exc:
        raise AuthError("Invalid or expired reset token.", status_code=400) from exc

    if payload.get("type") != "password_reset":
        raise AuthError("Invalid reset token.", status_code=400)

    email = payload.get("sub")
    if not email:
        raise AuthError("Invalid reset token.", status_code=400)

    user = await get_user_by_email(db, email)
    if user is None:
        raise AuthError("Invalid reset token.", status_code=400)

    user.password_hash = hash_password(new_password)
    await db.flush()
    await db.refresh(user)
    return user
