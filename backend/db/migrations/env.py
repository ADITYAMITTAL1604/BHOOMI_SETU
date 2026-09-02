"""Alembic environment configuration."""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool
from alembic import context

# Add the backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.database import Base
from app.models import *  # noqa: F403,F401 - import all models for autogenerate
from app.config import get_settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from settings
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# target_metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=False,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )
    # In offline mode, we don't use transactions
    context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Enable PostGIS extension if not present
        if "postgresql" in str(connectable.url):
            connection.execute("CREATE EXTENSION IF NOT EXISTS postgis")

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# For autogenerate without a database, use offline mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()