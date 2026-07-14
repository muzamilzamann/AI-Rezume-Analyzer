# AI Resume Analyzer — Backend

FastAPI + async SQLAlchemy + PostgreSQL backend for the AI Resume Analyzer.

See the root [`README.md`](../README.md) for full project documentation.

## Quick start

```bash
cp .env.example .env      # then fill in DATABASE_URL + JWT_SECRET_KEY
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API docs are available at http://localhost:8000/docs once running.
