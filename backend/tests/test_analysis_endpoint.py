"""HTTP-level tests for the analysis endpoints (DB-free via overrides)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_active_user, get_db
from app.api.v1.endpoints import analysis as analysis_module
from app.core.config import settings
from app.main import app
from app.models.analysis import Analysis
from app.models.user import User
from app.schemas.analysis import AIFeedback, ATSResult


def _make_analysis(resume_id) -> Analysis:
    return Analysis(
        id=uuid.uuid4(),
        resume_id=resume_id,
        overall_score=78.5,
        subscores={
            "completeness": 90.0, "formatting": 75.0, "keywords": 70.0,
            "length": 85.0, "impact": 60.0,
        },
        strengths=["Completeness is strong (90/100)."],
        weaknesses=["Impact & quantification is weak (60/100)."],
        recommendations=[
            "Start bullets with action verbs and quantify results (e.g. 'reduced latency 30%')."
        ],
        source="ats",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client(fake_user: User):
    async def _override_user():
        return fake_user

    async def _override_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_active_user] = _override_user
    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_run_analysis_endpoint(client: TestClient, fake_user: User) -> None:
    rid = uuid.uuid4()
    ats = ATSResult(
        overall_score=78.5,
        subscores=_make_analysis(rid).subscores,  # type: ignore[arg-type]
        strengths=[],
        weaknesses=[],
        recommendations=[],
    )
    analysis_module.run_ats_analysis = AsyncMock(return_value=(_make_analysis(rid), ats))
    try:
        response = client.post(
            f"{settings.api_v1_prefix}/analysis/run", json={"resume_id": str(rid)}
        )
    finally:
        from app.services import analysis_service

        analysis_module.run_ats_analysis = analysis_service.run_ats_analysis
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["resume_ats_score"] == 78.5
    assert body["analysis"]["overall_score"] == 78.5
    assert body["analysis"]["subscores"]["completeness"] == 90.0


def test_ai_feedback_endpoint(client: TestClient, fake_user: User) -> None:
    rid = uuid.uuid4()
    analysis = _make_analysis(rid)
    analysis.source = "ai"  # the service sets this from the feedback source
    feedback = AIFeedback(
        strengths=["Great header."],
        weaknesses=["Thin keywords."],
        recommendations=["Add more skills."],
        source="ai",
        model="gemini-2.0-flash",
    )
    # The real service overwrites these with the feedback content.
    analysis.strengths = feedback.strengths
    analysis.weaknesses = feedback.weaknesses
    analysis.recommendations = feedback.recommendations
    analysis_module.run_ai_feedback = AsyncMock(return_value=(analysis, feedback))
    try:
        response = client.post(
            f"{settings.api_v1_prefix}/analysis/ai-feedback", json={"resume_id": str(rid)}
        )
    finally:
        from app.services import analysis_service

        analysis_module.run_ai_feedback = analysis_service.run_ai_feedback
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["analysis"]["source"] == "ai"
    assert body["analysis"]["strengths"] == ["Great header."]
