"""
Data source and data broker management service.

Handles all business logic related to data sources including CRUD operations,
environment variables, data objects, and data broker operations.
"""

from typing import Any

import requests

from vulkan.data_source import DataSourceType
from vulkan.schemas import DataSourceSpec
from vulkan_engine.data.broker import DataBroker
from vulkan_engine.db import (
    DataObject,
    DataSource,
    DataSourceEnvVar,
    PolicyDataDependency,
    PolicyVersion,
    RunDataRequest,
    UploadedFile,
)
from vulkan_engine.exceptions import (
    DataBrokerException,
    DataBrokerRequestException,
    DataSourceAlreadyExistsException,
    DataSourceNotFoundException,
    InvalidDataSourceException,
)
from vulkan_engine.loaders import DataSourceLoader
from vulkan_engine.schemas import (
    DataBrokerRequest,
    DataBrokerResponse,
    DataObjectMetadata,
    DataSourceEnvVarBase,
)
from vulkan_engine.schemas import DataSource as DataSourceSchema
from vulkan_engine.schemas import (
    DataSourceEnvVar as DataSourceEnvVarSchema,
)
from vulkan_engine.services.base import BaseService


class DataSourceService(BaseService):
    """Service for managing data sources and data operations."""

    def __init__(self, db, logger=None):
        """
        Initialize data source service.

        Args:
            db: Database session
            logger: Optional logger
        """
        super().__init__(db, logger)
        self.data_source_loader = DataSourceLoader(db)

    def list_data_sources(
        self, include_archived: bool = False, project_id: str = None
    ) -> list[DataSource]:
        """
        List data sources, optionally filtered by project.

        Args:
            include_archived: Whether to include archived data sources
            project_id: Optional project UUID to filter by

        Returns:
            List of DataSource objects
        """
        return self.data_source_loader.list_data_sources(
            project_id=project_id, include_archived=include_archived
        )

    def create_data_source(
        self, spec: DataSourceSpec, project_id: str = None
    ) -> dict[str, str]:
        """
        Create a new data source.

        Args:
            spec: Data source specification
            project_id: Optional project UUID to associate with

        Returns:
            Dictionary with data_source_id

        Raises:
            DataSourceAlreadyExistsException: If data source name already exists
            InvalidDataSourceException: If data source configuration is invalid
        """
        # Check if data source already exists
        if self.data_source_loader.data_source_exists(
            name=spec.name, project_id=project_id
        ):
            raise DataSourceAlreadyExistsException(
                f"A Data Source with this name already exists: {spec.name}"
            )

        # Validate data source type
        if spec.source.source_type == DataSourceType.LOCAL_FILE:
            raise InvalidDataSourceException(
                "Local file data sources are not supported for remote execution"
            )

        # Handle registered file data source
        if spec.source.source_type == DataSourceType.REGISTERED_FILE:
            self._handle_registered_file(spec)

        # Create data source
        data_source = DataSource.from_spec(spec)
        data_source.project_id = project_id

        self.db.add(data_source)
        self.db.commit()

        return {"data_source_id": data_source.data_source_id}

    def get_data_source(
        self, data_source_id: str, project_id: str = None
    ) -> DataSource:
        """
        Get a data source by ID.

        Args:
            data_source_id: Data source UUID
            project_id: Optional project UUID to filter by

        Returns:
            DataSource object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        return self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )

    def delete_data_source(
        self, data_source_id: str, project_id: str = None
    ) -> dict[str, str]:
        """
        Delete (archive) a data source.

        Args:
            data_source_id: Data source UUID
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with data_source_id

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If data source is in use
        """
        # Get non-archived data source
        try:
            data_source = self.data_source_loader.get_data_source(
                data_source_id=data_source_id,
                project_id=project_id,
                include_archived=False,
            )
        except DataSourceNotFoundException:
            raise DataSourceNotFoundException(
                f"Tried to delete non-existent data source {data_source_id}"
            )

        # Check if data source is in use by policy versions
        policy_uses = (
            self.db.query(PolicyDataDependency, PolicyVersion)
            .join(PolicyVersion)
            .filter(
                PolicyDataDependency.data_source_id == data_source_id,
                PolicyVersion.archived == False,  # noqa: E712
            )
            .all()
        )

        if policy_uses:
            raise InvalidDataSourceException(
                f"Data source {data_source_id} is used by one or more policy versions"
            )

        # Check if data source has associated data objects
        objects = (
            self.db.query(DataObject).filter_by(data_source_id=data_source_id).all()
        )
        if objects:
            raise InvalidDataSourceException(
                f"Data source {data_source_id} has associated data objects"
            )

        data_source.archived = True
        self.db.commit()

        if self.logger:
            self.logger.system.info(f"Archived data source {data_source_id}")

        return {"data_source_id": data_source_id}

    def set_environment_variables(
        self,
        data_source_id: str,
        desired_variables: list[DataSourceEnvVarBase],
        project_id: str = None,
    ) -> dict[str, Any]:
        """
        Set environment variables for a data source.

        Args:
            data_source_id: Data source UUID
            desired_variables: List of environment variables to set
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with data_source_id and variables

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If variables are not supported
        """
        # Validate data source exists and is not archived
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        # Get existing variables
        existing_variables = (
            self.db.query(DataSourceEnvVar)
            .filter_by(data_source_id=data_source_id)
            .all()
        )

        # Remove variables not in desired list
        for var in existing_variables:
            if var.name not in {v.name for v in desired_variables}:
                self.db.delete(var)

        # Update or create variables
        existing_map = {v.name: v for v in existing_variables}
        for v in desired_variables:
            env_var = existing_map.get(v.name)
            if not env_var:
                env_var = DataSourceEnvVar(
                    data_source_id=data_source_id,
                    name=v.name,
                    value=v.value,
                )
                self.db.add(env_var)
            else:
                env_var.value = v.value

        self.db.commit()
        return {"data_source_id": data_source_id, "variables": desired_variables}

    def get_environment_variables(
        self, data_source_id: str, project_id: str = None
    ) -> list[DataSourceEnvVarSchema]:
        """
        Get environment variables for a data source.

        Args:
            data_source_id: Data source UUID
            project_id: Optional project UUID to filter by

        Returns:
            List of DataSourceEnvVar objects

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        # Validate data source exists and is not archived
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        return (
            self.db.query(DataSourceEnvVar)
            .filter_by(data_source_id=data_source_id)
            .all()
        )

    def list_data_objects(
        self, data_source_id: str, project_id: str = None
    ) -> list[DataObjectMetadata]:
        """
        List data objects for a data source.

        Args:
            data_source_id: Data source UUID
            project_id: Optional project UUID to filter by

        Returns:
            List of DataObjectMetadata objects

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        # Validate data source exists (include archived for data objects listing)
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )

        data_objects = (
            self.db.query(DataObject).filter_by(data_source_id=data_source_id).all()
        )

        return [
            DataObjectMetadata(
                data_object_id=obj.data_object_id,
                data_source_id=obj.data_source_id,
                key=obj.key,
                created_at=obj.created_at,
            )
            for obj in data_objects
        ]

    def get_data_object(
        self, data_source_id: str, data_object_id: str, project_id: str = None
    ) -> DataObject:
        """
        Get a specific data object.

        Args:
            data_source_id: Data source UUID
            data_object_id: Data object UUID
            project_id: Optional project UUID to filter by

        Returns:
            DataObject object

        Raises:
            DataSourceNotFoundException: If data source or data object doesn't exist
        """
        # Validate data source exists first
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )

        # Get the data object
        data_object = (
            self.db.query(DataObject)
            .filter_by(data_source_id=data_source_id, data_object_id=data_object_id)
            .first()
        )

        if not data_object:
            raise DataSourceNotFoundException("Data object not found")

        return data_object

    def request_data_from_broker(
        self, request: DataBrokerRequest, project_id: str = None
    ) -> DataBrokerResponse:
        """
        Request data through the data broker.

        Args:
            request: Data broker request
            project_id: Optional project UUID to filter by

        Returns:
            DataBrokerResponse object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If environment variables missing
        """
        # Find data source by name (include archived for broker requests)
        data_source = self.data_source_loader.get_data_source_by_name(
            name=request.data_source_name, project_id=project_id, include_archived=True
        )

        spec = DataSourceSchema.from_orm(data_source)

        # Initialize broker
        logger = self.logger.system if self.logger else None
        broker = DataBroker(db=self.db, logger=logger, spec=spec)

        # Get environment variables
        env_vars = (
            self.db.query(DataSourceEnvVar)
            .filter_by(data_source_id=spec.data_source_id)
            .all()
        )
        env_variables = {ev.name: ev.value for ev in env_vars} if env_vars else {}

        # Check for missing variables
        missing_vars = set(spec.variables or []) - set(env_variables.keys())
        if missing_vars:
            raise InvalidDataSourceException(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )

        try:
            # Get data through broker
            data = broker.get_data(request.configured_params, env_variables)

            # Record the request
            request_obj = RunDataRequest(
                run_id=request.run_id,
                data_object_id=data.data_object_id,
                data_source_id=spec.data_source_id,
                data_origin=data.origin,
            )
            self.db.add(request_obj)
            self.db.commit()

            return data

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.system.error(str(e))
            raise DataBrokerRequestException(str(e))
        except Exception as e:
            if self.logger:
                self.logger.system.error(str(e))
            raise DataBrokerException(str(e))

    def _handle_registered_file(self, spec: DataSourceSpec) -> None:
        """Handle registered file data source configuration."""
        uploaded_file = (
            self.db.query(UploadedFile)
            .filter_by(uploaded_file_id=spec.source.file_id)
            .first()
        )

        if not uploaded_file:
            raise InvalidDataSourceException(
                f"Uploaded file {spec.source.file_id} not found"
            )

        spec.source.path = uploaded_file.file_path
