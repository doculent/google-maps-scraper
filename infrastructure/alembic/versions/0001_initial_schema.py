"""Initial schema — scraped_entities table

Revision ID: 0001
Revises:
Create Date: 2026-02-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS scraper")

    op.create_table(
        "scraped_entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("website", sa.Text, nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("categories", JSONB, nullable=True),
        sa.Column("rating", sa.Float, nullable=True),
        sa.Column("reviews_count", sa.Integer, nullable=True),
        sa.Column("hours", JSONB, nullable=True),
        sa.Column("thumbnail", sa.Text, nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("extra_data", JSONB, nullable=True),
        sa.Column("scrape_query", sa.Text, nullable=True),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        schema="scraper",
    )

    op.create_index(
        "ix_scraped_entities_source", "scraped_entities", ["source"], schema="scraper"
    )
    op.create_index(
        "ix_scraped_entities_source_id", "scraped_entities", ["source_id"], schema="scraper"
    )
    op.create_index(
        "ix_scraped_entities_source_source_id",
        "scraped_entities",
        ["source", "source_id"],
        schema="scraper",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scraped_entities_source_source_id",
        table_name="scraped_entities",
        schema="scraper",
    )
    op.drop_index(
        "ix_scraped_entities_source_id",
        table_name="scraped_entities",
        schema="scraper",
    )
    op.drop_index(
        "ix_scraped_entities_source",
        table_name="scraped_entities",
        schema="scraper",
    )
    op.drop_table("scraped_entities", schema="scraper")
