"""Rule-based ATS scoring engine.

Evaluates a resume across five dimensions and produces an overall score plus
actionable strengths / weaknesses / recommendations. Deterministic and fully
offline — no AI calls. The Gemini-powered narrative feedback arrives in Week 4.
"""

from __future__ import annotations

import re
from typing import Any

from app.schemas.analysis import ATSResult, ATSSubscores

# Subscore weights (sum to 100).
WEIGHTS = {
    "completeness": 25,
    "formatting": 20,
    "keywords": 20,
    "length": 15,
    "impact": 20,
}

ACTION_VERBS = {
    "led", "built", "developed", "designed", "managed", "implemented", "created",
    "improved", "increased", "reduced", "launched", "delivered", "architected",
    "optimized", "engineered", "drove", "established", "spearheaded", "automated",
    "migrated", "integrated", "coordinated", "analyzed", "researched", "shipped",
    "maintained", "scaled", "streamlined", "mentored", "founded",
}

SECTION_HEADERS = {
    "experience", "education", "skills", "projects", "summary",
    "professional experience", "work experience", "technical skills",
    "work history", "employment", "academic", "certifications",
}

_BULLET_RE = re.compile(r"^\s*[•·\*\-\u2013]\s")


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _score_completeness(parsed: dict[str, Any]) -> float:
    score = 0.0
    if parsed.get("name"):
        score += 15
    if parsed.get("email"):
        score += 15
    if parsed.get("phone"):
        score += 10
    if parsed.get("links"):
        score += 10
    skills = parsed.get("skills") or []
    if len(skills) >= 5:
        score += 20
    elif len(skills) >= 1:
        score += 10
    if parsed.get("experience"):
        score += 15
    if parsed.get("education"):
        score += 10
    if parsed.get("projects"):
        score += 5
    return _clamp(score)


def _score_formatting(raw_text: str, parsed: dict[str, Any]) -> float:
    if not raw_text:
        return 0.0
    lines = [ln for ln in raw_text.splitlines() if ln.strip()]
    score = 0.0

    # Section presence (up to 40)
    headers_found = 0
    for ln in lines:
        key = ln.strip().lower().rstrip(":")
        if key in SECTION_HEADERS and len(ln.split()) <= 4:
            headers_found += 1
    score += min(headers_found, 4) * 10

    # Bullet usage (up to 20)
    bullet_lines = sum(1 for ln in lines if _BULLET_RE.match(ln))
    if bullet_lines >= 5:
        score += 20
    elif bullet_lines >= 1:
        score += 10

    # Average line length sanity (up to 20)
    if lines:
        avg_len = sum(len(ln) for ln in lines) / len(lines)
        if 40 <= avg_len <= 110:
            score += 20
        elif 30 <= avg_len <= 130:
            score += 10

    # Avoid excessive ALL-CAPS lines (up to 20)
    if lines:
        caps_lines = sum(
            1 for ln in lines if len(ln) > 4 and ln == ln.upper() and any(c.isalpha() for c in ln)
        )
        caps_ratio = caps_lines / len(lines)
        if caps_ratio <= 0.1:
            score += 20
        elif caps_ratio <= 0.25:
            score += 10

    # Penalize when parsed skills missing (signals poor structure)
    if not parsed.get("skills"):
        score = min(score, 60.0)

    return _clamp(score)


def _score_keywords(parsed: dict[str, Any], raw_text: str) -> float:
    skills = parsed.get("skills") or []
    count = len(skills)
    if count == 0:
        return 10.0
    if count <= 5:
        base = 40.0
    elif count <= 10:
        base = 70.0
    elif count <= 20:
        base = 90.0
    else:
        base = 100.0
    # Density bonus: skills per 100 words should be reasonable (not stuffed).
    words = max(len(raw_text.split()), 1)
    density = (count / words) * 100
    if density > 12:  # keyword stuffing
        base -= 15
    return _clamp(base)


def _score_length(parsed: dict[str, Any]) -> float:
    wc = parsed.get("word_count") or 0
    if wc < 150:
        return 30.0
    if wc < 300:
        return 70.0
    if wc <= 800:
        return 100.0
    if wc <= 1000:
        return 85.0
    return 65.0


def _score_impact(raw_text: str) -> float:
    if not raw_text:
        return 0.0
    lower = raw_text.lower()
    words = lower.split()
    if not words:
        return 0.0

    # Action verb usage (up to 50)
    verb_hits = sum(1 for w in words if w.strip(".,;:()") in ACTION_VERBS)
    verb_ratio = verb_hits / len(words)
    verb_score = _clamp(verb_ratio * 1000, 0, 50)  # ~5% verbs -> max

    # Quantified achievements: numbers, %, $, xN (up to 50)
    metrics = len(re.findall(r"\d+%|\$\d|\b\d{2,}\b|\b\d+x\b", raw_text))
    metric_score = _clamp(metrics * 7, 0, 50)

    return _clamp(verb_score + metric_score)


def _overall(subscores: ATSSubscores) -> float:
    total = (
        subscores.completeness * WEIGHTS["completeness"]
        + subscores.formatting * WEIGHTS["formatting"]
        + subscores.keywords * WEIGHTS["keywords"]
        + subscores.length * WEIGHTS["length"]
        + subscores.impact * WEIGHTS["impact"]
    )
    return round(total / 100.0, 1)


def compute_ats(raw_text: str | None, parsed_data: dict[str, Any] | None) -> ATSResult:
    parsed = parsed_data or {}
    text = raw_text or ""

    subscores = ATSSubscores(
        completeness=round(_score_completeness(parsed), 1),
        formatting=round(_score_formatting(text, parsed), 1),
        keywords=round(_score_keywords(parsed, text), 1),
        length=round(_score_length(parsed), 1),
        impact=round(_score_impact(text), 1),
    )
    overall = _overall(subscores)

    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []

    label_map = {
        "completeness": "Completeness",
        "formatting": "Formatting",
        "keywords": "Keyword coverage",
        "length": "Length",
        "impact": "Impact & quantification",
    }
    value_map = {
        "completeness": subscores.completeness,
        "formatting": subscores.formatting,
        "keywords": subscores.keywords,
        "length": subscores.length,
        "impact": subscores.impact,
    }

    for key in label_map:
        val = value_map[key]
        if val >= 80:
            strengths.append(f"{label_map[key]} is strong ({val:.0f}/100).")
        elif val < 60:
            weaknesses.append(f"{label_map[key]} is weak ({val:.0f}/100).")

    # Targeted recommendations
    if value_map["completeness"] < 80:
        missing = []
        if not parsed.get("phone"):
            missing.append("a phone number")
        if not parsed.get("links"):
            missing.append("LinkedIn/GitHub links")
        if not parsed.get("projects"):
            missing.append("a projects section")
        if missing:
            recommendations.append("Add " + ", ".join(missing) + " to your header/sections.")
    if value_map["formatting"] < 80:
        recommendations.append("Use clear section headers and bullet points for readability.")
    if value_map["keywords"] < 80:
        recommendations.append(
            f"Include more relevant technical keywords (found {len(parsed.get('skills') or [])})."
        )
    if value_map["length"] < 80:
        wc = parsed.get("word_count") or 0
        if wc < 300:
            recommendations.append("Resume is short — expand to 300–800 words with more detail.")
        else:
            recommendations.append("Trim the resume to keep it within 300–800 words.")
    if value_map["impact"] < 80:
        recommendations.append(
            "Start bullets with action verbs and quantify results (e.g. 'reduced latency 30%')."
        )
    if not recommendations:
        recommendations.append("Great resume! Keep tailoring keywords to each job description.")

    return ATSResult(
        overall_score=overall,
        subscores=subscores,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
    )
