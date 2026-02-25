"""Add scrape_jobs table for job history tracking

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scrape_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("max_places", sa.Integer, nullable=True),
        sa.Column("lang", sa.String(10), nullable=False, server_default="en"),
        sa.Column("results_count", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="scraper",
    )

    op.create_index(
        "ix_scrape_jobs_status", "scrape_jobs", ["status"], schema="scraper"
    )
    op.create_index(
        "ix_scrape_jobs_created_at", "scrape_jobs", ["created_at"], schema="scraper"
    )


def downgrade() -> None:
    op.drop_index("ix_scrape_jobs_created_at", table_name="scrape_jobs", schema="scraper")
    op.drop_index("ix_scrape_jobs_status", table_name="scrape_jobs", schema="scraper")
    op.drop_table("scrape_jobs", schema="scraper")
