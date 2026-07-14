"""Tests for the job-match service."""

from __future__ import annotations

from app.services.job_match_service import compute_match


def test_compute_match_finds_overlap() -> None:
    resume_skills = ["Python", "FastAPI", "PostgreSQL", "React", "TypeScript"]
    jd = (
        "We're hiring a full-stack engineer. You need Python, FastAPI, PostgreSQL, "
        "AWS, Docker, and Kubernetes. React experience is a plus."
    )
    result = compute_match(resume_skills, jd)

    assert result.match_score > 0
    assert "Python" in result.matching_skills
    assert "FastAPI" in result.matching_skills
    assert "AWS" in result.missing_skills
    assert "Docker" in result.missing_skills
    assert result.recommendations


def test_compute_match_no_jd_skills() -> None:
    result = compute_match(["Python", "React"], "We want a friendly person who likes cats.")
    assert result.match_score == 0.0
    assert result.missing_skills == []


def test_compute_match_perfect_overlap() -> None:
    result = compute_match(["Python", "React"], "Need Python and React developer.")
    assert result.match_score == 100.0
    assert set(result.matching_skills) == {"Python", "React"}
    assert result.missing_skills == []


def test_compute_match_score_is_ratio() -> None:
    # 2 of 4 JD skills present -> 50%
    result = compute_match(["Python", "React"], "Python, React, AWS, Docker required.")
    assert result.match_score == 50.0
    assert len(result.matching_skills) == 2
    assert len(result.missing_skills) == 2


def test_compute_match_extra_skills() -> None:
    result = compute_match(["Python", "Go", "Rust"], "Need Python developer.")
    assert "Python" in result.matching_skills
    assert set(result.extra_skills) == {"Go", "Rust"}
