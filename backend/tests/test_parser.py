"""Tests for the resume parser."""

from __future__ import annotations

from app.services.parser import extract_text, parse_resume
from tests._helpers import build_docx

DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_extracts_contact_and_links(sample_resume_text: str) -> None:
    parsed = parse_resume(sample_resume_text)
    assert parsed.email == "jane.doe@email.com"
    assert parsed.phone and "415" in parsed.phone.replace(" ", "")
    assert "https://linkedin.com/in/janedoe" in parsed.links
    assert "https://github.com/janedoe" in parsed.links


def test_guesses_name(sample_resume_text: str) -> None:
    parsed = parse_resume(sample_resume_text)
    assert parsed.name == "Jane Doe"


def test_detects_skills(sample_resume_text: str) -> None:
    parsed = parse_resume(sample_resume_text)
    skills_lower = {s.lower() for s in parsed.skills}
    for expected in ["python", "fastapi", "postgresql", "react", "typescript", "aws", "docker"]:
        assert expected in skills_lower


def test_splits_sections(sample_resume_text: str) -> None:
    parsed = parse_resume(sample_resume_text)
    assert any("Acme Corp" in e for e in parsed.experience)
    assert any("Beta Inc" in e for e in parsed.experience)
    assert any("UC Berkeley" in e for e in parsed.education)
    assert any("Resume Analyzer" in e for e in parsed.projects)


def test_word_count(sample_resume_text: str) -> None:
    parsed = parse_resume(sample_resume_text)
    assert parsed.word_count > 0


def test_short_skill_matchers_avoid_false_positives() -> None:
    # The word "going" must not register the "Go" skill, nor "c..." random text.
    text = "I am going to the store and use CSharp not the letter c"
    parsed = parse_resume(text)
    skills_lower = {s.lower() for s in parsed.skills}
    assert "go" not in skills_lower
    assert "golang" not in skills_lower
    assert "c#" not in skills_lower  # written as "CSharp", not in catalogue form


def test_extract_text_from_docx(sample_resume_text: str) -> None:
    data = build_docx(sample_resume_text)
    text = extract_text(data, DOCX_CT, "r.docx")
    assert "Jane Doe" in text
    assert "FastAPI" in text


def test_extract_text_unsupported_returns_empty() -> None:
    assert extract_text(b"hello", "text/plain", "file.txt") == ""
