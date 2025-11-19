"""
Data source and data broker management service.

Handles all business logic related to data sources including CRUD operations,
environment variables, data objects, and data broker operations.
"""

from typing import Any
from urllib.parse import urlparse

import requests
from sqlalchemy import func, select
from vulkan.credentials import (
    validate_credential_type,
    validate_no_reserved_credentials_in_templates,
)
from vulkan.data_source import DataSourceStatus, DataSourceType
from vulkan.schemas import DataSourceSpec

from vulkan_engine.data.broker import DataBroker
from vulkan_engine.db import (
    Component,
    DataObject,
    DataSource,
    DataSourceCredential,
    DataSourceEnvVar,
    PolicyVersion,
    RunDataRequest,
    Workflow,
    WorkflowDataDependency,
)
from vulkan_engine.exceptions import (
    DataBrokerException,
    DataBrokerRequestException,
    DataObjectNotFoundException,
    DataSourceAlreadyExistsException,
    DataSourceNotFoundException,
    InvalidDataSourceException,
)
from vulkan_engine.loaders import DataSourceLoader
from vulkan_engine.logging import get_logger
from vulkan_engine.schemas import (
    DataBrokerRequest,
    DataBrokerResponse,
    DataObjectMetadata,
    DataSourceCredentialBase,
    DataSourceEnvVarBase,
)
from vulkan_engine.schemas import DataSource as DataSourceSchema
from vulkan_engine.schemas import DataSourceCredential as DataSourceCredentialSchema
from vulkan_engine.schemas import DataSourceEnvVar as DataSourceEnvVarSchema
from vulkan_engine.services.auth_handler import AuthHandler
from vulkan_engine.services.base import BaseService


class DataSourceService(BaseService):
    """Service for managing data sources and data operations."""

    def __init__(self, db, redis_cache=None):
        """
        Initialize data source service.

        Args:
            db: Database session
            redis_cache: Optional Redis client for OAuth token caching
        """
        super().__init__(db)
        self.data_source_loader = DataSourceLoader(db)
        self.redis_cache = redis_cache
        self.logger = get_logger(__name__)

    def _validate_data_source_type(self, spec: DataSourceSpec) -> None:
        """
        Validate that the data source type is supported for remote execution.

        Args:
            spec: Data source specification

        Raises:
            InvalidDataSourceException: If data source type is LOCAL_FILE
        """
        if spec.source.source_type == DataSourceType.LOCAL_FILE:
            raise InvalidDataSourceException(
                "Local file data sources are not supported for remote execution"
            )

    def _validate_reserved_credentials(self, spec: DataSourceSpec) -> None:
        """
        Validate that reserved credential names (CLIENT_ID, CLIENT_SECRET)
        are not used in templates.

        Args:
            spec: Data source specification

        Raises:
            InvalidDataSourceException: If reserved names are used in templates
        """
        # Only validate HTTPSource with auth configured
        if spec.source.source_type != DataSourceType.HTTP:
            return

        if not hasattr(spec.source, "auth") or spec.source.auth is None:
            return

        # Extract all environment variables from templates
        env_vars = spec.source.extract_env_vars()

        try:
            validate_no_reserved_credentials_in_templates(
                env_vars, error_context="templates"
            )
        except ValueError as e:
            raise InvalidDataSourceException(str(e))

    def list_data_sources(
        self, include_archived: bool = False, project_id: str = None, status: str = None
    ) -> list[DataSourceSchema]:
        """
        List data sources, optionally filtered by project and status.

        Args:
            include_archived: Whether to include archived data sources
            project_id: Optional project UUID to filter by
            status: Optional status to filter by (e.g., 'PUBLISHED', 'DRAFT')

        Returns:
            List of DataSource objects
        """
        # Convert string status to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = DataSourceStatus[status.upper()]
            except (KeyError, AttributeError):
                # If status is invalid, return empty list
                return []

        data_sources = self.data_source_loader.list_data_sources(
            project_id=project_id, include_archived=include_archived, status=status_enum
        )
        return [DataSourceSchema.from_orm(ds) for ds in data_sources]

    def create_data_source(
        self, spec: DataSourceSpec, project_id: str = None
    ) -> DataSourceSchema:
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
        self._validate_data_source_type(spec)

        # Validate reserved credential names not used in templates
        self._validate_reserved_credentials(spec)

        # Create data source
        data_source = DataSource.from_spec(spec)
        data_source.project_id = project_id

        self.db.add(data_source)
        self.db.commit()

        return DataSourceSchema.from_orm(data_source)

    def get_data_source(
        self, data_source_id: str, project_id: str = None
    ) -> DataSourceSchema:
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
        data_source = self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )
        return DataSourceSchema.from_orm(data_source)

    def update_data_source(
        self, data_source_id: str, spec: DataSourceSpec, project_id: str = None
    ) -> DataSourceSchema:
        """
        Update an existing data source.

        Published data sources have restricted update capabilities to prevent
        breaking changes in production. Only metadata, caching config, timeout,
        and retry policy can be modified for published data sources.

        Args:
            data_source_id: Data source UUID
            spec: Updated data source specification
            project_id: Optional project UUID to filter by

        Returns:
            Updated DataSource object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If data source configuration is invalid
        """
        data_source = self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        # Validate data source type
        self._validate_data_source_type(spec)

        # Validate reserved credential names not used in templates
        self._validate_reserved_credentials(spec)

        # Published data sources can only update metadata, caching, timeout, and retry policy
        # This prevents breaking changes to data sources that are in production use
        if data_source.is_published():
            data_source.description = spec.description
            data_source.config_metadata = spec.metadata
            data_source.caching_enabled = spec.caching.enabled
            data_source.caching_ttl = spec.caching.calculate_ttl()
            if spec.source.get("timeout") is not None:
                data_source.source["timeout"] = spec.source.get("timeout")
            if spec.source.get("retry") is not None:
                data_source.source["retry"] = spec.source.get("retry")
        else:
            data_source.update_from_spec(spec)

        self.db.commit()

        self.logger.info("updated_data_source", data_source_id=data_source_id)

        return DataSourceSchema.from_orm(data_source)

    def delete_data_source(
        self, data_source_id: str, project_id: str = None
    ) -> dict[str, str]:
        """
        Delete or archive a data source based on its status.


        Args:
            data_source_id: Data source UUID
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with data_source_id

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
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

        # Hard delete for DRAFT data sources
        if data_source.status == DataSourceStatus.DRAFT:
            self.db.delete(data_source)
            self.db.commit()

            self.logger.info(
                "hard_deleted_draft_data_source",
                data_source_id=data_source_id,
            )

            return {"data_source_id": data_source_id}

        # Archive for PUBLISHED data sources, check if in use first
        # used in policy versions
        stmt = (
            select(PolicyVersion)
            .select_from(WorkflowDataDependency)
            .join(Workflow)
            .join(PolicyVersion)
            .where(
                (WorkflowDataDependency.data_source_id == data_source_id)
                & (PolicyVersion.archived.is_(False))
            )
        )
        policy_uses = self.db.execute(stmt).all()

        if policy_uses:
            raise InvalidDataSourceException(
                f"Data source {data_source_id} is used by one or more policy versions"
            )

        # used in components
        stmt_component = (
            select(Component)
            .select_from(WorkflowDataDependency)
            .join(Workflow)
            .join(Component)
            .where(
                (WorkflowDataDependency.data_source_id == data_source_id)
                & (Component.archived.is_(False))
            )
        )
        component_uses = self.db.execute(stmt_component).all()

        if component_uses:
            raise InvalidDataSourceException(
                f"Data source {data_source_id} is used by one or more components"
            )

        # has associated data objects
        objects = (
            self.db.query(DataObject).filter_by(data_source_id=data_source_id).all()
        )
        if objects:
            raise InvalidDataSourceException(
                f"Data source {data_source_id} has associated data objects"
            )

        data_source.status = DataSourceStatus.ARCHIVED
        self.db.commit()

        self.logger.info(
            "archived_data_source",
            data_source_id=data_source_id,
            status=data_source.status.value,
        )

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
        _ = self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        # Block reserved credential names, use /credentials endpoint
        variable_names = {v.name for v in desired_variables}

        try:
            validate_no_reserved_credentials_in_templates(
                variable_names, error_context="environment variables"
            )
        except ValueError as e:
            raise InvalidDataSourceException(
                f"{str(e)} Please use the /credentials endpoint instead: PUT /data-sources/{{id}}/credentials"
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
            value_to_store = v.value

            env_var = existing_map.get(v.name)
            if not env_var:
                env_var = DataSourceEnvVar(
                    data_source_id=data_source_id,
                    name=v.name,
                    value=value_to_store,
                )
                self.db.add(env_var)
            else:
                env_var.value = value_to_store

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

        env_vars = (
            self.db.query(DataSourceEnvVar)
            .filter_by(data_source_id=data_source_id)
            .all()
        )

        return [DataSourceEnvVarSchema.model_validate(var) for var in env_vars]

    def set_credentials(
        self, data_source_id: str, credentials: list[DataSourceCredentialBase],  project_id: str | None = None,
    ) -> list[DataSourceCredentialSchema]:
        """
        Set credentials for a data source

        Args:
            data_source_id: Data source UUID
            credentials: List of credentials (CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD)

        Returns:
            List of saved DataSourceCredential objects

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If credential types are invalid or auth not configured
        """
        # Validate data source exists, raise DataSourceNotFoundException if not found
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        for cred in credentials:
            try:
                validate_credential_type(cred.credential_type)
            except ValueError as e:
                raise InvalidDataSourceException(str(e))

        saved_credentials = []
        for cred in credentials:
            # Check if credential already exists
            existing = (
                self.db.query(DataSourceCredential)
                .filter_by(
                    data_source_id=data_source_id, credential_type=cred.credential_type,
                )
                .first()
            )

            if existing:
                existing.value = cred.value
                existing.last_updated_at = func.now()
                saved_credentials.append(existing)
            else:
                new_credential = DataSourceCredential(
                    data_source_id=data_source_id,
                    credential_type=cred.credential_type,
                    value=cred.value,
                )
                self.db.add(new_credential)
                saved_credentials.append(new_credential)

        self.db.commit()

        for cred in saved_credentials:
            self.db.refresh(cred)

        return [
            DataSourceCredentialSchema.model_validate(cred)
            for cred in saved_credentials
        ]

    def get_credentials(self, data_source_id: str, project_id: str | None = None) -> list[DataSourceCredentialSchema]:
        """
        Get credentials for a data source

        Args:
            data_source_id: Data source UUID

        Returns:
            List of DataSourceCredential objects

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        credentials = (
            self.db.query(DataSourceCredential)
            .filter_by(data_source_id=data_source_id)
            .all()
        )

        return [DataSourceCredentialSchema.model_validate(cred) for cred in credentials]

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
            raise DataObjectNotFoundException(
                f"Data object {data_object_id} not found in data source {data_source_id}"
            )

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

        # Validate request configuration for HTTP data sources
        if spec.source.source_type == DataSourceType.HTTP:
            _validate_url_scheme(spec.source.url)

        # Initialize broker
        # DataBroker uses old logging system, pass None
        broker = DataBroker(db=self.db, logger=None, spec=spec)

        # Get environment variables and credentials from database
        env_variables = _load_env_vars(self.db, spec.data_source_id)
        credentials = _load_credentials(self.db, spec.data_source_id)

        # Check for missing variables
        missing_vars = set(spec.variables or []) - set(env_variables.keys())
        if missing_vars:
            raise InvalidDataSourceException(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )

        # Handle authentication if configured
        auth_headers = None
        auth_params = None

        if hasattr(spec.source, "auth") and spec.source.auth:
            auth_handler = AuthHandler(
                auth_config=spec.source.auth,
                data_source_id=spec.data_source_id,
                credentials=credentials,
                cache=self.redis_cache,
            )
            auth_headers = auth_handler.get_auth_headers()

        try:
            # Get data through broker
            data = broker.get_data(
                request.configured_params,
                env_variables,
                auth_headers=auth_headers,
                auth_params=auth_params,
            )

            # Record the request with timing information
            request_obj = RunDataRequest(
                run_id=request.run_id,
                data_object_id=data.data_object_id,
                data_source_id=spec.data_source_id,
                data_origin=data.origin,
                start_time=data.start_time,
                end_time=data.end_time,
                error=data.error,
            )
            self.db.add(request_obj)
            self.db.commit()

            return data

        except (
            requests.exceptions.RequestException,
            requests.exceptions.HTTPError,
        ) as e:
            self.logger.error("data_broker_request_error", error=str(e), exc_info=True)
            raise DataBrokerRequestException(str(e))
        except Exception as e:
            self.logger.error("data_broker_error", error=str(e), exc_info=True)
            raise DataBrokerException(str(e))

    def publish_data_source(
        self, data_source_id: str, project_id: str = None
    ) -> DataSourceSchema:
        """
        Publish a data source.

        Publishing marks a data source as ready for production use. Published
        data sources have restricted update capabilities to prevent breaking
        changes.

        Args:
            data_source_id: Data source UUID
            project_id: Optional project UUID to filter by

        Returns:
            DataSource object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        # Get data source
        data_source = self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        # Check if already published (idempotency)
        if data_source.is_published():
            return DataSourceSchema.from_orm(data_source)

        # Publish, validation is handled by DB constraints and schema validation
        data_source.status = DataSourceStatus.PUBLISHED
        self.db.commit()

        self.logger.info("published_data_source", data_source_id=data_source_id)

        return DataSourceSchema.from_orm(data_source)


# Helper


def _load_env_vars(db, data_source_id: str) -> dict[str, str]:
    """
    Load environment variables from database.

    Args:
        db: Database session
        data_source_id: Data source UUID

    Returns:
        Dictionary of name -> value pairs
    """
    env_vars = {}
    all_vars = db.query(DataSourceEnvVar).filter_by(data_source_id=data_source_id).all()
    for var in all_vars:
        if var.value is None:
            value = ""
        elif isinstance(var.value, str):
            value = var.value
        else:
            value = str(var.value)
        env_vars[var.name] = value
    return env_vars


def _load_credentials(db, data_source_id: str) -> dict[str, str]:
    """
    Load authentication credentials from database.

    Args:
        db: Database session
        data_source_id: Data source UUID

    Returns:
        Dictionary of credential_type -> value pairs
    """
    credentials_rows = (
        db.query(DataSourceCredential).filter_by(data_source_id=data_source_id).all()
    )
    return {cred.credential_type.value: cred.value for cred in credentials_rows}


def _validate_url_scheme(url: str) -> None:
    """
    Validate URL scheme is http or https.

    Args:
        url: URL to validate

    Raises:
        InvalidDataSourceException: If scheme is invalid
    """

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise InvalidDataSourceException(f"Invalid URL format: {str(e)}")

    if parsed.scheme not in ["http", "https"]:
        raise InvalidDataSourceException(
            f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed"
        )
