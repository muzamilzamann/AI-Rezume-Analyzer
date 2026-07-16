FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# NOTE: build context is the repository root (works with Railway's root context,
# Render's dockerContext, docker-compose, and GitHub Actions `docker build .`).
# Install dependencies first (cached layer)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev --extra parsing --extra cloud --extra gemini

# Copy application code
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini backend/README.md ./

# Install the project itself
RUN uv sync --frozen --no-dev --extra parsing --extra cloud --extra gemini

EXPOSE 8000

# Run migrations on startup, then launch the API.
# $PORT is injected by Railway/Render; default to 8000 for docker-compose/local.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
