"""add resume parsing columns

Revision ID: 0002_resume_parsed_data
Revises: 0001_initial_schema
Create Date: 2026-07-14 00:00:01.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_resume_parsed_data"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("storage_id", sa.String(length=512), nullable=True))
    op.add_column("resumes", sa.Column("content_type", sa.String(length=100), nullable=True))
    op.add_column("resumes", sa.Column("raw_text", sa.Text(), nullable=True))
    op.add_column(
        "resumes",
        sa.Column("parsed_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("resumes", "parsed_data")
    op.drop_column("resumes", "raw_text")
    op.drop_column("resumes", "content_type")
    op.drop_column("resumes", "storage_id")
