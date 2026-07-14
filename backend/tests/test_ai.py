"""Tests for the AI feedback service (rule-based fallback + JSON parsing)."""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.schemas.analysis import ATSResult, ATSSubscores
from app.services.ai_service import _parse_gemini_json, generate_feedback, is_gemini_configured


@pytest.fixture
def ats_result() -> ATSResult:
    return ATSResult(
        overall_score=72.0,
        subscores=ATSSubscores(completeness=90, formatting=70, keywords=60, length=80, impact=50),
        strengths=[],
        weaknesses=[],
        recommendations=[],
    )


def test_rule_based_when_not_configured(
    sample_resume_text: str, ats_result: ATSResult
) -> None:
    assert is_gemini_configured() is False
    parsed = {
        "name": "Jane", "email": "j@x.com",
        "skills": ["Python", "FastAPI"], "experience": ["x"],
    }
    fb = generate_feedback(sample_resume_text, parsed, ats_result)
    assert fb.source == "rule-based"
    assert fb.strengths and fb.weaknesses and fb.recommendations
    assert any("action verb" in r.lower() for r in fb.recommendations)


def test_empty_text_feedback(sample_resume_text: str) -> None:
    fb = generate_feedback("", None, None)
    assert fb.source == "rule-based"
    assert fb.weaknesses
    assert "text" in fb.weaknesses[0].lower()


def test_parse_gemini_json_plain(sample_resume_text: str) -> None:
    raw = '{"strengths": ["a"], "weaknesses": ["b"], "recommendations": ["c"]}'
    parsed = _parse_gemini_json(raw)
    assert parsed == {"strengths": ["a"], "weaknesses": ["b"], "recommendations": ["c"]}


def test_parse_gemini_json_fenced() -> None:
    raw = (
        'Here you go:\n```json\n'
        '{"strengths": ["x", "y"], "weaknesses": [], "recommendations": ["z"]}\n```'
    )
    parsed = _parse_gemini_json(raw)
    assert parsed["strengths"] == ["x", "y"]
    assert parsed["recommendations"] == ["z"]


def test_parse_gemini_json_with_prose() -> None:
    raw = (
        'Sure! {"strengths": ["a"], "weaknesses": ["b"], '
        '"recommendations": ["c"]} hope this helps'
    )
    parsed = _parse_gemini_json(raw)
    assert parsed["strengths"] == ["a"]


def test_gemini_failure_falls_back(
    monkeypatch, sample_resume_text: str, ats_result: ATSResult
) -> None:
    # Pretend Gemini is configured but the call blows up.
    monkeypatch.setattr(settings, "gemini_api_key", "fake-key")

    def _boom(_prompt):
        raise RuntimeError("network down")

    monkeypatch.setattr("app.services.ai_service._call_gemini", _boom)
    fb = generate_feedback(sample_resume_text, {"skills": ["Python"]}, ats_result)
    assert fb.source == "rule-based"
    assert fb.recommendations
