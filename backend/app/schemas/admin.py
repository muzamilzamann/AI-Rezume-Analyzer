"""Admin-related Pydantic schemas."""

from pydantic import BaseModel, ConfigDict


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    total_resumes: int
    total_analyses: int
    total_job_matches: int
    avg_ats_score: float | None


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: str
    resume_count: int


class UserActiveUpdate(BaseModel):
    is_active: bool
