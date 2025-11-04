"""
Data source loader for data access layer.
"""

from typing import List

from sqlalchemy.orm import Query
from vulkan.data_source import DataSourceStatus

from vulkan_engine.db import DataSource
from vulkan_engine.exceptions import DataSourceNotFoundException
from vulkan_engine.loaders.base import BaseLoader


class DataSourceLoader(BaseLoader):
    """Loader for DataSource resources."""

    def _apply_status_filter(
        self, query: Query, include_archived: bool = False
    ) -> Query:
        """
        Apply status filter to exclude ARCHIVED data sources.

        DataSource uses a status enum (DRAFT, PUBLISHED, ARCHIVED) instead of
        a boolean archived field. This method filters out ARCHIVED status unless
        explicitly requested.

        Args:
            query: SQLAlchemy query object
            include_archived: Whether to include ARCHIVED status data sources

        Returns:
            Query with status filter applied
        """
        if not include_archived:
            return query.filter(
                DataSource.status.in_(
                    [DataSourceStatus.DRAFT, DataSourceStatus.PUBLISHED]
                )
            )
        return query

    def get_data_source(
        self, data_source_id: str, project_id: str = None, include_archived: bool = True
    ) -> DataSource:
        """
        Get a data source by ID, filtered by project.

        Args:
            data_source_id: Data source UUID
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived data sources (default: True)

        Returns:
            DataSource object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist or doesn't belong to specified project
        """
        query = self.db.query(DataSource).filter(
            DataSource.data_source_id == data_source_id,
            DataSource.project_id == project_id,
        )

        # Apply status filter to exclude ARCHIVED data sources if needed
        query = self._apply_status_filter(query, include_archived)

        data_source = query.first()
        if not data_source:
            raise DataSourceNotFoundException(f"Data source {data_source_id} not found")

        return data_source

    def get_data_source_by_name(
        self, name: str, project_id: str = None, include_archived: bool = True
    ) -> DataSource:
        """
        Get a data source by name, filtered by project.

        Args:
            name: Data source name
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived data sources (default: True)

        Returns:
            DataSource object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist or doesn't belong to specified project
        """
        query = self.db.query(DataSource).filter(
            DataSource.name == name,
            DataSource.project_id == project_id,
        )

        # Apply status filter to exclude ARCHIVED data sources if needed
        query = self._apply_status_filter(query, include_archived)

        data_source = query.first()
        if not data_source:
            raise DataSourceNotFoundException(f"Data source '{name}' not found")

        return data_source

    def list_data_sources(
        self,
        project_id: str = None,
        include_archived: bool = False,
        status: DataSourceStatus | None = None,
    ) -> List[DataSource]:
        """
        List data sources with optional filtering.

        Args:
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived data sources
            status: Optional status enum to filter by (e.g., DataSourceStatus.PUBLISHED)

        Returns:
            List of DataSource objects
        """
        query = self.db.query(DataSource).filter(DataSource.project_id == project_id)

        # If specific status requested, use it directly (uses composite index)
        if status:
            query = query.filter(DataSource.status == status)
        # Otherwise, apply archived filter
        elif not include_archived:
            query = query.filter(
                DataSource.status.in_(
                    [DataSourceStatus.DRAFT, DataSourceStatus.PUBLISHED]
                )
            )

        return query.all()

    def data_source_exists(
        self, data_source_id: str = None, name: str = None, project_id: str = None
    ) -> bool:
        """
        Check if a data source exists by ID or name.

        Args:
            data_source_id: Optional data source UUID
            name: Optional data source name
            project_id: Optional project UUID to filter by

        Returns:
            True if data source exists, False otherwise
        """
        if not data_source_id and not name:
            raise ValueError("Either data_source_id or name must be provided")

        query = self.db.query(DataSource).filter(DataSource.project_id == project_id)

        if data_source_id:
            query = query.filter(DataSource.data_source_id == data_source_id)
        elif name:
            query = query.filter(DataSource.name == name)

        # Only check non-archived data sources for existence
        query = self._apply_status_filter(query, include_archived=False)

        return query.first() is not None
