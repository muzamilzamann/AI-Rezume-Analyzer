"""Job-match Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, Field


class JobMatchCreate(BaseModel):
    resume_id: str
    job_title: str | None = None
    job_description: str = Field(..., min_length=10, max_length=20000)


class JobMatchResult(BaseModel):
    match_score: float
    matching_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    extra_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class JobMatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    job_title: str | None
    job_description: str
    match_score: float
    matching_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]
    recommendations: list[str]
    created_at: str
