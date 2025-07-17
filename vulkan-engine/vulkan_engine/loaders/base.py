"""
Base loader class with common functionality for all resource loaders.
"""

from sqlalchemy.orm import Query, Session


class BaseLoader:
    """Base class for all resource loaders."""

    def __init__(self, db: Session):
        """
        Initialize the loader with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def _apply_archived_filter(
        self, query: Query, include_archived: bool = False
    ) -> Query:
        """
        Apply archived filter to a query.

        Args:
            query: SQLAlchemy query object
            include_archived: Whether to include archived records

        Returns:
            Query with archived filter applied
        """
        if not include_archived:
            return query.filter_by(archived=False)
        return query
