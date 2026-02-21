import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gmaps_scraper_server.models.entity import ScrapedEntity


class EntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ScrapedEntity) -> ScrapedEntity:
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def create_many(self, entities: List[ScrapedEntity]) -> List[ScrapedEntity]:
        self._session.add_all(entities)
        await self._session.commit()
        return entities

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ScrapedEntity]:
        result = await self._session.execute(
            select(ScrapedEntity).where(ScrapedEntity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_by_source(self, source: str, limit: int = 100) -> List[ScrapedEntity]:
        result = await self._session.execute(
            select(ScrapedEntity).where(ScrapedEntity.source == source).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_source_id(self, source: str, source_id: str) -> List[ScrapedEntity]:
        result = await self._session.execute(
            select(ScrapedEntity).where(
                ScrapedEntity.source == source,
                ScrapedEntity.source_id == source_id,
            )
        )
        return list(result.scalars().all())
