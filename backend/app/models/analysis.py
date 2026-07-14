"""Analysis model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.resume import Resume


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    strengths: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    weaknesses: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    recommendations: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    resume: Mapped["Resume"] = relationship("Resume", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<Analysis for {self.resume_id}>"
