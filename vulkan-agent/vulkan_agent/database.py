"""Database connection and session management for Vulkan Agent."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


class DatabaseManager:
    """Simple database manager for SQLite."""

    def __init__(self, db_path: str = None):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file. If None, uses default.
        """
        if db_path is None:
            # Default to data directory in the same location as the app
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "vulkan_agent.db")

        self.db_path = db_path

        # Create SQLite engine
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Initialize database schema
        self._initialize_db()

    def _initialize_db(self):
        """Create database tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
_db_manager = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        # Check for custom database path from environment
        db_path = os.getenv("VULKAN_DB_PATH")
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def reset_database_manager():
    """Reset the global database manager (useful for testing)."""
    global _db_manager
    _db_manager = None
