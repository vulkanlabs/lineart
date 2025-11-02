"""
Database migration utilities for vulkan-engine.

This module provides a clean API for running database migrations using Alembic.
It accepts configuration objects rather than reading environment variables directly.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from vulkan_engine.config import DatabaseConfig
from vulkan_engine.db import Base


def run_migrations(database_config: DatabaseConfig) -> None:
    """
    Run Alembic migrations to upgrade database to the latest version.

    Args:
        database_config: DatabaseConfig instance with connection details

    Raises:
        FileNotFoundError: If alembic.ini cannot be found
        Exception: If migration fails
    """
    # Locate alembic.ini relative to this module
    # When installed, __file__ points to site-packages/vulkan_engine/migrations.py
    # and alembic.ini is at site-packages/vulkan_engine/alembic.ini
    vulkan_engine_root = Path(__file__).parent
    alembic_ini_path = vulkan_engine_root / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(
            f"Alembic configuration not found at {alembic_ini_path}"
        )

    # Create Alembic configuration and set the database URL programmatically
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", database_config.connection_string)

    # Run migrations to latest version
    command.upgrade(alembic_cfg, "head")


def create_initial_schema(database_config: DatabaseConfig) -> None:
    """
    Create the initial database schema directly using SQLAlchemy metadata.

    This is an alternative to running migrations, useful for testing or
    initial setup scenarios. For production, prefer run_migrations().

    Args:
        database_config: DatabaseConfig instance with connection details
    """
    engine = create_engine(database_config.connection_string, echo=False)
    Base.metadata.create_all(bind=engine)
    engine.dispose()
