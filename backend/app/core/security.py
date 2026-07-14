"""Password hashing and JWT token utilities."""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


# --------------------------------------------------------------------------- #
# Password hashing (bcrypt)
# --------------------------------------------------------------------------- #
def hash_password(raw_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(raw_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- #
# JWT tokens
# --------------------------------------------------------------------------- #
def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    payload = {"sub": subject, "type": "access", **(extra or {})}
    return _create_token(payload, timedelta(minutes=settings.access_token_expire_minutes))


def create_password_reset_token(email: str) -> str:
    return _create_token(
        {"sub": email, "type": "password_reset"},
        timedelta(minutes=settings.reset_token_expire_minutes),
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
