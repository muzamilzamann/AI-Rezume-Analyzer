"""add job_matches table

Revision ID: 0004_job_matches
Revises: 0003_analysis_scores
Create Date: 2026-07-14 00:00:03.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_job_matches"
down_revision: str | None = "0003_analysis_scores"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("matching_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("extra_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["resume_id"], ["resumes.id"], name="fk_job_matches_resume_id_resumes", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_job_matches"),
    )
    op.create_index("ix_job_matches_resume_id", "job_matches", ["resume_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_matches_resume_id", table_name="job_matches")
    op.drop_table("job_matches")
