import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from alembic import context

# Import your models
from models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Create fresh Settings instance to get updated environment variables
    from config import Settings
    fresh_settings = Settings()
    config.set_main_option("sqlalchemy.url", fresh_settings.database_url)

    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(database_url: str) -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # Create engine directly with database_url from fresh Settings
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Create fresh Settings instance to get updated environment variables
    import os
    print(f"DEBUG: DB_HOST from os.environ = {os.environ.get('DB_HOST', 'NOT SET')}")

    from config import Settings
    fresh_settings = Settings()
    print(f"DEBUG: fresh_settings.db_host = {fresh_settings.db_host}")
    print(f"DEBUG: fresh_settings.database_url = {fresh_settings.database_url}")

    # Run migrations with fresh database_url
    asyncio.run(run_async_migrations(fresh_settings.database_url))


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
