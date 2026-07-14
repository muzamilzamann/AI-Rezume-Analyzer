"""Analysis-related Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ATSSubscores(BaseModel):
    completeness: float
    formatting: float
    keywords: float
    length: float
    impact: float


class ATSResult(BaseModel):
    overall_score: float
    subscores: ATSSubscores
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AnalysisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    overall_score: float | None
    subscores: dict[str, float] | None
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    source: str
    created_at: str


class AnalysisRunResponse(BaseModel):
    analysis: AnalysisRead
    resume_ats_score: float


class AIFeedback(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    source: str = "rule-based"  # "ai" | "rule-based"
    model: str = ""
