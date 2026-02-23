import asyncio
import os
import sys
from logging.config import fileConfig

# Add project root to sys.path so gmaps_scraper_server is importable
# env.py lives at infrastructure/alembic/env.py — two levels up is the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import sqlalchemy as sa
from alembic import context
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

# Alembic Config object — provides access to values in alembic.ini
config = context.config

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import metadata so Alembic can detect schema changes (autogenerate)
from gmaps_scraper_server.models import Base  # noqa: E402

target_metadata = Base.metadata

DATABASE_URL = (
    "postgresql+asyncpg://"
    f"{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}"
    f"/{os.environ['POSTGRES_NAME']}"
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection, outputs SQL)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema="scraper",
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    # Schema must exist before Alembic can create scraper.alembic_version
    connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS scraper"))
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",
        version_table_schema="scraper",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database."""
    connectable = create_async_engine(DATABASE_URL, echo=False)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
