"""AI feedback generation powered by Google Gemini.

When ``GEMINI_API_KEY`` is configured, the resume is sent to Gemini with a
recruiter-style prompt and the structured JSON response is parsed into
strengths / weaknesses / recommendations. When the key is absent or the call
fails, a deterministic rule-based fallback (derived from the parsed data and ATS
result) is returned so the feature stays useful in any environment.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.schemas.analysis import AIFeedback, ATSResult

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def is_gemini_configured() -> bool:
    return bool(settings.gemini_api_key)


def _build_prompt(raw_text: str, parsed: dict[str, Any], ats: ATSResult | None) -> str:
    skills = ", ".join(parsed.get("skills") or []) or "none detected"
    experience = "\n".join(f"- {e}" for e in (parsed.get("experience") or [])[:5]) or "none"
    subscores = ats.subscores.model_dump() if ats else {}
    overall = ats.overall_score if ats else "unknown"
    return f"""You are an expert technical recruiter and resume coach.

Analyze the resume below and produce actionable, recruiter-grade feedback.
Return ONLY a JSON object with three keys, each a list of 3-6 concise strings:
- "strengths": what makes this resume effective
- "weaknesses": specific shortcomings
- "recommendations": concrete, prioritized improvements

Context:
- Detected ATS score: {overall}/100
- Subscores: {json.dumps(subscores)}
- Detected skills: {skills}
- Experience entries:
{experience}

Resume text:
\"\"\"
{raw_text[:6000]}
\"\"\"
"""


def _parse_gemini_json(text: str) -> dict[str, list[str]]:
    """Extract the JSON object from a Gemini response (handles fenced code)."""
    candidate = text.strip()
    fence = _JSON_FENCE_RE.search(candidate)
    if fence:
        candidate = fence.group(1)
    # Fallback: grab the outermost {...} block.
    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1:
            candidate = candidate[start : end + 1]
    data = json.loads(candidate)
    return {
        "strengths": [str(x) for x in data.get("strengths", [])],
        "weaknesses": [str(x) for x in data.get("weaknesses", [])],
        "recommendations": [str(x) for x in data.get("recommendations", [])],
    }


def _call_gemini(prompt: str) -> dict[str, list[str]]:
    from google import genai
    from google.genai import types as gtypes

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=gtypes.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.4,
            max_output_tokens=1024,
        ),
    )
    return _parse_gemini_json(response.text or "")


def _rule_based_feedback(parsed: dict[str, Any], ats: ATSResult | None) -> dict[str, list[str]]:
    skills = parsed.get("skills") or []
    subs = ats.subscores if ats else None

    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []

    if parsed.get("name") and parsed.get("email"):
        strengths.append("Clear contact header with name and email.")
    if len(skills) >= 8:
        strengths.append(f"Strong technical keyword coverage ({len(skills)} skills detected).")
    elif len(skills) >= 1:
        strengths.append("Includes a recognizable skills section.")
    if subs and subs.impact >= 60:
        strengths.append("Good use of action verbs and quantified achievements.")
    if parsed.get("experience"):
        strengths.append("Experience section is present and structured.")

    if not parsed.get("phone"):
        weaknesses.append("Missing phone number — some ATS filters expect it.")
    if not parsed.get("links"):
        weaknesses.append("No LinkedIn/GitHub links — recruiters look for these.")
    if len(skills) < 5:
        weaknesses.append("Thin keyword coverage may not match ATS filters.")
    if subs and subs.length < 60:
        weaknesses.append("Resume length is outside the recommended 300–800 word range.")
    if subs and subs.impact < 60:
        weaknesses.append("Bullets lack quantified impact metrics.")

    recommendations.append("Tailor keywords to each job description by mirroring its language.")
    recommendations.append("Start every bullet with a strong action verb (led, built, reduced).")
    recommendations.append("Quantify results wherever possible (%, $, time saved, scale).")
    if len(skills) < 10:
        recommendations.append("Add a dedicated technical skills block with 10–20 relevant terms.")
    recommendations.append("Keep the resume to one page and 300–800 words.")

    return {"strengths": strengths, "weaknesses": weaknesses, "recommendations": recommendations}


def generate_feedback(
    raw_text: str | None,
    parsed_data: dict[str, Any] | None,
    ats: ATSResult | None = None,
) -> AIFeedback:
    parsed = parsed_data or {}
    text = raw_text or ""

    if not text:
        return AIFeedback(
            strengths=[],
            weaknesses=["No extractable text was found in this resume."],
            recommendations=["Upload a text-based PDF or DOCX (not a scanned image)."],
            source="rule-based",
        )

    if is_gemini_configured():
        try:
            prompt = _build_prompt(text, parsed, ats)
            data = _call_gemini(prompt)
            return AIFeedback(
                strengths=data["strengths"],
                weaknesses=data["weaknesses"],
                recommendations=data["recommendations"],
                source="ai",
                model=settings.gemini_model,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini call failed, falling back to rule-based feedback: %s", exc)

    data = _rule_based_feedback(parsed, ats)
    return AIFeedback(**data, source="rule-based", model="rule-based")
