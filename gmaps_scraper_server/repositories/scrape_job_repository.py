import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gmaps_scraper_server.models.scrape_job import ScrapeJob


class ScrapeJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: ScrapeJob) -> ScrapeJob:
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: str,
        *,
        results_count: Optional[int] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[ScrapeJob]:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = status
        if results_count is not None:
            job.results_count = results_count
        if error_message is not None:
            job.error_message = error_message
        if completed_at is not None:
            job.completed_at = completed_at
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[ScrapeJob]:
        result = await self._session.execute(
            select(ScrapeJob).where(ScrapeJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs(self, limit: int = 50, offset: int = 0) -> List[ScrapeJob]:
        result = await self._session.execute(
            select(ScrapeJob)
            .order_by(ScrapeJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
