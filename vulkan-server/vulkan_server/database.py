"""
Database initialization for vulkan-server.

This module handles database table creation and initialization using
the models defined in vulkan-engine.
"""

import sys

from sqlalchemy import create_engine
from vulkan_engine.config import VulkanEngineConfig
from vulkan_engine.db import Base

from vulkan_server.config import load_vulkan_engine_config


def init_database(config: VulkanEngineConfig) -> None:
    """
    Initialize the database by creating all tables.

    Args:
        config: VulkanEngineConfig instance with database configuration
    """
    engine = create_engine(config.database.connection_string, echo=True)
    Base.metadata.create_all(bind=engine)


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
