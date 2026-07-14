"""Shared test fixtures."""

from __future__ import annotations

import pytest

from app.models.user import User


@pytest.fixture
def fake_user() -> User:
    return User(
        name="Test User",
        email="test@example.com",
        password_hash="x",
        is_active=True,
        is_superuser=False,
    )


@pytest.fixture
def sample_resume_text() -> str:
    return """\
Jane Doe
San Francisco, CA | jane.doe@email.com | (415) 555-1234
https://linkedin.com/in/janedoe | https://github.com/janedoe

Summary
Senior backend engineer with 6 years of experience building scalable APIs.

Experience
Senior Software Engineer at Acme Corp
- Built REST APIs with Python, FastAPI and PostgreSQL
- Led migration to Kubernetes and Docker

Software Engineer at Beta Inc
- Developed React and TypeScript frontend
- Worked with AWS and Redis

Education
B.Sc. in Computer Science, UC Berkeley
2015 - 2019

Projects
Resume Analyzer
- AI tool using Python, LangChain and PyTorch
"""
