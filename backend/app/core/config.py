"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse, urlunparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    app_name: str = "AI Resume Analyzer"
    environment: Literal["dev", "staging", "prod"] = "dev"
    api_v1_prefix: str = "/api/v1"
    frontend_url: str = "http://localhost:5173"

    # Database. Accepts Neon's plain postgresql://...?sslmode=require string.
    database_url: str = Field(
        ..., description="PostgreSQL URL, e.g. postgresql://user:pass@host/db"
    )
    db_ssl_mode: Literal[
        "disable", "allow", "prefer", "require", "verify-ca", "verify-full"
    ] = "require"

    # JWT / Auth
    jwt_secret_key: str = Field(..., description="Secret used to sign JWTs")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day
    reset_token_expire_minutes: int = 30

    # AI - Google Gemini
    gemini_api_key: str = ""

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    @model_validator(mode="after")
    def _normalize_database_url(self) -> "Settings":
        url = self.database_url.strip()
        # Map postgres(ql):// -> postgresql+asyncpg:// for SQLAlchemy async
        if url.startswith("postgresql+asyncpg://"):
            pass
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://") :]
        elif url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://") :]
        # Strip psycopg-style sslmode=... (asyncpg uses the ssl connect arg instead)
        if "sslmode=" in url:
            parsed = urlparse(url)
            params = [
                kv for kv in (parsed.query.split("&") if parsed.query else [])
                if kv and not kv.startswith("sslmode=")
            ]
            url = urlunparse(parsed._replace(query="&".join(params)))
        self.database_url = url
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [self.frontend_url]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
