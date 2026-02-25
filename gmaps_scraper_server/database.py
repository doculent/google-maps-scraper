import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from gmaps_scraper_server.config import load_secrets

load_secrets()

DATABASE_URL = (
    "postgresql+asyncpg://"
    f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}"
    f"/{os.environ['POSTGRES_NAME']}"
)

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async session generator for use with FastAPI Depends."""
    async with AsyncSessionLocal() as session:
        yield session
