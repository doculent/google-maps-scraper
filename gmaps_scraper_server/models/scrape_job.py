import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from gmaps_scraper_server.models.entity import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScrapeJob(Base):
    """Tracks every scrape request for history and auditing."""

    __tablename__ = "scrape_jobs"
    __table_args__ = {"schema": "scraper"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    max_places: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lang: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    results_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, index=True
    )
