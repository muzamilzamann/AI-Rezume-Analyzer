FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev --extra parsing --extra cloud --extra gemini

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini README.md ./

# Install the project itself
RUN uv sync --frozen --no-dev --extra parsing --extra cloud --extra gemini

EXPOSE 8000

# Run migrations on startup, then launch the API.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
