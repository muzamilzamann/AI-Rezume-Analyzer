"""Resume-related Pydantic schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParsedResume(BaseModel):
    """Structured data extracted from a resume."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    word_count: int = 0


class ResumeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResumeRead(ResumeBase):
    id: str
    user_id: str
    file_url: str
    file_name: str
    content_type: str | None = None
    ats_score: float | None = None
    raw_text: str | None = None
    parsed_data: dict[str, Any] | None = None
    created_at: str


class ResumeSummary(ResumeBase):
    """Lightweight resume representation for lists."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    ats_score: float | None = None
    created_at: str
    skills: list[str] = Field(default_factory=list)


class ResumeUploadResponse(BaseModel):
    resume: ResumeRead
    parsed: ParsedResume
