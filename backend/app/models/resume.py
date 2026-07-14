"""Resume model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis
    from app.models.job_match import JobMatch
    from app.models.user import User


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Cloudinary public_id (or local filename) used to delete the asset later.
    storage_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Raw extracted text (kept for ATS scoring / AI features in later weeks).
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structured extraction: {name, email, phone, skills, education, ...}
    parsed_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="resumes")
    analysis: Mapped["Analysis | None"] = relationship(
        "Analysis", back_populates="resume", uselist=False, cascade="all, delete-orphan"
    )
    job_matches: Mapped[list["JobMatch"]] = relationship(
        "JobMatch", back_populates="resume", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Resume {self.file_name}>"
