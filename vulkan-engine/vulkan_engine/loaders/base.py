"""
Base loader class with common functionality for all resource loaders.
"""

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseLoader:
    """Base class for all resource loaders."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the loader with a database session.

        Args:
            db: SQLAlchemy async database session
        """
        self.db = db

    def _apply_archived_filter(
        self, query: Select, include_archived: bool = False
    ) -> Select:
        """
        Apply archived filter to a query.

        Args:
            query: SQLAlchemy select statement
            include_archived: Whether to include archived records

        Returns:
            Select statement with archived filter applied
        """
        if not include_archived:
            return query.filter_by(archived=False)
        return query
