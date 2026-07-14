"""Async SQLAlchemy database engine and session factory."""

import ssl as _ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _build_connect_args() -> dict:
    if settings.db_ssl_mode == "disable":
        return {}
    ctx = _ssl.create_default_context()
    # "require"/"prefer"/"allow" -> encrypt but do not verify (Neon accepts this)
    if settings.db_ssl_mode in {"allow", "prefer", "require"}:
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
    # verify-ca / verify-full keep the secure defaults
    return {"ssl": ctx}


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args=_build_connect_args(),
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a scoped async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
