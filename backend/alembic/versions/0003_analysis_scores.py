"""add analysis score columns

Revision ID: 0003_analysis_scores
Revises: 0002_resume_parsed_data
Create Date: 2026-07-14 00:00:02.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_analysis_scores"
down_revision: str | None = "0002_resume_parsed_data"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("overall_score", sa.Float(), nullable=True))
    op.add_column(
        "analyses",
        sa.Column("subscores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "analyses",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="ats"),
    )


def downgrade() -> None:
    op.drop_column("analyses", "source")
    op.drop_column("analyses", "subscores")
    op.drop_column("analyses", "overall_score")
