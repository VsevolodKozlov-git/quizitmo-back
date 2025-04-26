# alembic/env.py

import os
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from app.db.base_class import Base  # your Base
from app.models import *  # import all your models so Base.metadata is populated

# this is the Alembic Config object
config = context.config

# set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# the target metadata for 'autogenerate'
target_metadata = Base.metadata


def get_url():
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "786811")
    db = os.getenv("POSTGRES_DB", "diplom")
    server = os.getenv("POSTGRES_SERVER", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+asyncpg://{user}:{password}@{server}:{port}/{db}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode: emit SQL to stdout."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode: connect, then run."""
    # update the alembic config with our async URL
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    # create an async engine
    connectable = create_async_engine(
        configuration["sqlalchemy.url"],
        poolclass=pool.NullPool,
        future=True,
    )

    # run the migrations within an asyncio context
    async with connectable.connect() as connection:  # type: Connection
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def do_run_migrations(sync_connection: Connection) -> None:
    """Callback for run_sync(): configure Alembic and run."""
    context.configure(connection=sync_connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # dispatch to async runner
    asyncio.run(run_migrations_online())
