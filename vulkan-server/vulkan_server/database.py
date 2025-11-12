"""
Database initialization for vulkan-server.

This module handles database schema migrations using Alembic.
"""

import sys

from vulkan_engine.config import VulkanEngineConfig
from vulkan_engine.migrations import run_migrations

from vulkan_server.config import load_vulkan_engine_config


def init_database(config: VulkanEngineConfig) -> None:
    """
    Initialize the database by running Alembic migrations.

    Args:
        config: VulkanEngineConfig instance with database configuration
    """
    run_migrations(config.database)


def main():
    """Main entry point for database initialization."""
    try:
        # Load configuration from environment variables
        config = load_vulkan_engine_config()

        init_database(config)
        print("Database initialization completed successfully")

    except Exception as e:
        print(f"Database initialization failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
