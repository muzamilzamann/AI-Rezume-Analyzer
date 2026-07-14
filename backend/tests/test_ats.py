"""Tests for the ATS scoring engine."""

from __future__ import annotations

from app.services.ats_service import compute_ats


def test_compute_ats_returns_scored_result(sample_resume_text: str) -> None:
    parsed = {
        "name": "Jane Doe",
        "email": "jane.doe@email.com",
        "phone": "(415) 555-1234",
        "skills": ["Python", "FastAPI", "PostgreSQL", "React", "TypeScript", "AWS", "Docker"],
        "education": ["B.Sc. in Computer Science, UC Berkeley"],
        "experience": ["Senior Software Engineer at Acme Corp"],
        "projects": ["Resume Analyzer"],
        "links": ["https://linkedin.com/in/janedoe"],
        "word_count": len(sample_resume_text.split()),
    }
    result = compute_ats(sample_resume_text, parsed)

    assert 0 <= result.overall_score <= 100
    assert 0 <= result.subscores.completeness <= 100
    assert result.subscores.completeness == 100.0  # all fields present
    assert result.strengths  # at least one strength
    assert isinstance(result.recommendations, list) and result.recommendations


def test_compute_ats_empty_resume() -> None:
    result = compute_ats("", {})
    assert result.overall_score < 50
    assert result.subscores.completeness == 0.0
    assert result.weaknesses  # weak across the board


def test_overall_is_weighted_average() -> None:
    parsed = {
        "name": "X",
        "email": "x@x.com",
        "phone": "1",
        "skills": ["a", "b", "c", "d", "e"],
        "education": ["y"],
        "experience": ["z"],
        "projects": ["p"],
        "links": ["l"],
        "word_count": 400,
    }
    text = "Built and shipped. Reduced latency 30%. Led team of 5.\n" * 20
    result = compute_ats(text, parsed)
    # Manually recompute to confirm weighting
    s = result.subscores
    expected = (
        s.completeness * 25 + s.formatting * 20 + s.keywords * 20 + s.length * 15 + s.impact * 20
    ) / 100
    assert abs(result.overall_score - round(expected, 1)) < 0.05


def test_low_impact_when_no_metrics() -> None:
    result = compute_ats("worked on things and did stuff\n" * 30, {"word_count": 210})
    assert result.subscores.impact < 20
