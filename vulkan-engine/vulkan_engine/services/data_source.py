"""
Data source and data broker management service.

Handles all business logic related to data sources including CRUD operations,
environment variables, and data broker operations.
"""

import os
import time
from typing import Any
from urllib.parse import urlparse

import httpx
import jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from vulkan.credentials import (
    validate_credential_type,
    validate_no_reserved_credentials_in_templates,
)
from vulkan.data_source import DataSourceStatus, DataSourceType
from vulkan.schemas import DataSourceSpec

from vulkan_engine.db import (
    Component,
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
    DataSourceAlreadyExistsException,
    DataSourceNotFoundException,
    InvalidDataSourceException,
)
from vulkan_engine.loaders import DataSourceLoader
from vulkan_engine.logging import get_logger
from vulkan_engine.schemas import (
    DataBrokerRequest,
    DataBrokerResponse,
    DataObjectOrigin,
    DataSourceCredentialBase,
    DataSourceEnvVarBase,
)
from vulkan_engine.schemas import DataSource as DataSourceSchema
from vulkan_engine.schemas import DataSourceCredential as DataSourceCredentialSchema
from vulkan_engine.schemas import DataSourceEnvVar as DataSourceEnvVarSchema
from vulkan_engine.services.base import BaseService


class DataSourceService(BaseService):
    """Service for managing data sources and data operations."""

    def __init__(
        self,
        db: AsyncSession,
        redis_cache=None,
        data_broker_url: str | None = None,
        jwt_secret: str | None = None,
        jwt_issuer: str | None = None,
        jwt_audience: str | None = None,
    ):
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
        broker_url = data_broker_url or os.getenv("DATA_BROKER_URL")
        self.data_broker_url = broker_url.rstrip("/") if broker_url else None
        self.jwt_secret = jwt_secret or os.getenv("VULKAN_JWT_SECRET")
        self.jwt_issuer = jwt_issuer or os.getenv("VULKAN_JWT_ISSUER")
        self.jwt_audience = jwt_audience or os.getenv(
            "VULKAN_JWT_AUDIENCE", "data-broker-service"
        )
        self.jwt_ttl = int(os.getenv("VULKAN_JWT_TTL", "3600"))

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

    async def list_data_sources(
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

        data_sources = await self.data_source_loader.list_data_sources(
            project_id=project_id, include_archived=include_archived, status=status_enum
        )
        return [DataSourceSchema.from_orm(ds) for ds in data_sources]

    async def create_data_source(
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
        if await self.data_source_loader.data_source_exists(
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
        await self.db.commit()

        return DataSourceSchema.from_orm(data_source)

    async def get_data_source(
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
        data_source = await self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )
        return DataSourceSchema.from_orm(data_source)

    async def get_data_source_by_name(
        self,
        data_source_name: str,
        project_id: str | None = None,
        include_secrets: bool = False,
    ) -> DataSourceSchema | dict[str, Any]:
        """
        Get a data source by name with optional secret material.

        Args:
            data_source_name: Data source name
            project_id: Optional project UUID to filter by
            include_secrets: Whether to include env vars and credentials
        """
        data_source = await self.data_source_loader.get_data_source_by_name(
            name=data_source_name,
            project_id=project_id,
            include_archived=True,
        )
        spec = DataSourceSchema.from_orm(data_source)

        if not include_secrets:
            return spec

        env_variables = await _load_env_vars(self.db, spec.data_source_id)
        credentials = await _load_credentials(self.db, spec.data_source_id)

        return {
            "data_source_spec": self._build_data_source_spec(spec),
            "env_variables": env_variables,
            "credentials": credentials,
        }

    async def update_data_source(
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
        data_source = await self.data_source_loader.get_data_source(
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

        await self.db.commit()
        await self.db.refresh(data_source)

        self.logger.info("updated_data_source", data_source_id=data_source_id)

        return DataSourceSchema.from_orm(data_source)

    async def delete_data_source(
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
            data_source = await self.data_source_loader.get_data_source(
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
            await self.db.delete(data_source)
            await self.db.commit()

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
        result = await self.db.execute(stmt)
        policy_uses = list(result.scalars().all())

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
        component_result = await self.db.execute(stmt_component)
        component_uses = list(component_result.scalars().all())

        if component_uses:
            raise InvalidDataSourceException(
                f"Data source {data_source_id} is used by one or more components"
            )

        data_source.status = DataSourceStatus.ARCHIVED
        await self.db.commit()

        self.logger.info(
            "archived_data_source",
            data_source_id=data_source_id,
            status=data_source.status.value,
        )

        return {"data_source_id": data_source_id}

    async def set_environment_variables(
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
        _ = await self.data_source_loader.get_data_source(
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
        env_var_stmt = select(DataSourceEnvVar).filter_by(data_source_id=data_source_id)
        env_var_result = await self.db.execute(env_var_stmt)
        existing_variables = list(env_var_result.scalars().all())

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

        await self.db.commit()
        return {"data_source_id": data_source_id, "variables": desired_variables}

    async def get_environment_variables(
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
        await self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        env_var_stmt = select(DataSourceEnvVar).filter_by(data_source_id=data_source_id)
        env_var_result = await self.db.execute(env_var_stmt)
        env_vars = list(env_var_result.scalars().all())

        return [DataSourceEnvVarSchema.model_validate(var) for var in env_vars]

    async def set_credentials(
        self, data_source_id: str, credentials: list[DataSourceCredentialBase]
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
        await self.data_source_loader.get_data_source(
            data_source_id=data_source_id, include_archived=False
        )

        for cred in credentials:
            try:
                validate_credential_type(cred.credential_type)
            except ValueError as e:
                raise InvalidDataSourceException(str(e))

        saved_credentials = []
        for cred in credentials:
            # Check if credential already exists
            cred_stmt = select(DataSourceCredential).filter_by(
                data_source_id=data_source_id, credential_type=cred.credential_type
            )
            cred_result = await self.db.execute(cred_stmt)
            existing = cred_result.scalar_one_or_none()

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

        await self.db.commit()

        for cred in saved_credentials:
            await self.db.refresh(cred)

        return [
            DataSourceCredentialSchema.model_validate(cred)
            for cred in saved_credentials
        ]

    async def get_credentials(
        self, data_source_id: str
    ) -> list[DataSourceCredentialSchema]:
        """
        Get credentials for a data source

        Args:
            data_source_id: Data source UUID

        Returns:
            List of DataSourceCredential objects

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        await self.data_source_loader.get_data_source(
            data_source_id=data_source_id, include_archived=False
        )

        cred_stmt = select(DataSourceCredential).filter_by(
            data_source_id=data_source_id
        )
        cred_result = await self.db.execute(cred_stmt)
        credentials = list(cred_result.scalars().all())

        return [DataSourceCredentialSchema.model_validate(cred) for cred in credentials]

    async def list_data_objects(
        self, data_source_id: str, project_id: str = None
    ) -> list[Any]:
        """
        Data objects are now managed by the data-broker-service cache.

        This method is kept for backward compatibility but no longer returns
        cached objects from the application database.
        """
        await self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )
        return []

    async def request_data_from_broker(
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
            DataBrokerException: If broker is not configured
        """
        project_context = project_id or getattr(request, "project_id", None)

        # Find data source by name (include archived for broker requests)
        data_source = await self.data_source_loader.get_data_source_by_name(
            name=request.data_source_name,
            project_id=project_context,
            include_archived=True,
        )

        spec = DataSourceSchema.from_orm(data_source)

        # Validate request configuration for HTTP data sources
        if spec.source.source_type == DataSourceType.HTTP:
            _validate_url_scheme(spec.source.url)

        if not self.data_broker_url:
            raise DataBrokerException(
                "Data broker service is not configured for this environment"
            )

        env_variables = await _load_env_vars(self.db, spec.data_source_id)
        credentials = await _load_credentials(self.db, spec.data_source_id)

        # Check for missing variables
        missing_vars = set(spec.variables or []) - set(env_variables.keys())
        if missing_vars:
            raise InvalidDataSourceException(
                f"Missing environment variables: {', '.join(missing_vars)}"
            )

        merged_env = {
            key: "" if value is None else str(value)
            for key, value in {**credentials, **env_variables}.items()
        }

        payload = self._build_broker_payload(spec, request, merged_env)
        headers = self._build_broker_headers()

        request_start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.data_broker_url}/v1/fetch-data",
                    json=payload,
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            self.logger.error(
                "data_broker_request_error",
                error=str(e),
                status_code=e.response.status_code if e.response else None,
                response_text=e.response.text if e.response else None,
                exc_info=True,
            )
            raise DataBrokerRequestException(str(e)) from e
        except httpx.HTTPError as e:
            self.logger.error("data_broker_error", error=str(e), exc_info=True)
            raise DataBrokerException(str(e)) from e

        broker_response = response.json()
        origin = broker_response.get("origin", DataObjectOrigin.REQUEST.value)
        try:
            origin_enum = DataObjectOrigin(origin)
        except ValueError:
            origin_enum = DataObjectOrigin.REQUEST

        duration = broker_response.get("duration")
        computed_start = request_start if duration is not None else None
        computed_end = request_start + duration if duration is not None else None

        request_obj = RunDataRequest(
            run_id=request.run_id,
            data_object_id=broker_response.get("data_object_id"),
            data_source_id=spec.data_source_id,
            data_origin=origin_enum,
            start_time=computed_start,
            end_time=computed_end,
            error=broker_response.get("error"),
        )
        self.db.add(request_obj)
        await self.db.commit()

        return DataBrokerResponse(
            data_object_id=broker_response.get("data_object_id"),
            origin=origin_enum,
            key=broker_response.get("key"),
            value=broker_response.get("value"),
            start_time=computed_start,
            end_time=computed_end,
            duration=duration,
            error=broker_response.get("error"),
        )

    def _build_broker_payload(
        self,
        spec: DataSourceSchema,
        request: DataBrokerRequest,
        env_variables: dict[str, str],
    ) -> dict[str, Any]:
        """Construct payload for data broker fetch."""
        resolved_env = {
            key: "" if value is None else str(value)
            for key, value in {
                **env_variables,
                **(request.env_variables or {}),
            }.items()
        }
        return {
            "data_source_spec": self._build_data_source_spec(spec),
            "configured_params": request.configured_params,
            "env_variables": resolved_env,
            "run_id": request.run_id,
        }

    def _build_broker_headers(self) -> dict[str, str] | None:
        """Generate Authorization headers for broker access when configured."""
        required = [self.jwt_secret, self.jwt_issuer, self.jwt_audience]
        if not all(required):
            return None

        now = int(time.time())
        payload = {
            "iss": self.jwt_issuer,
            "aud": self.jwt_audience,
            "iat": now,
            "exp": now + self.jwt_ttl,
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}

    def _build_data_source_spec(self, spec: DataSourceSchema) -> dict[str, Any]:
        """Build broker-friendly data source spec."""
        ttl = spec.caching.calculate_ttl()
        caching_ttl = ttl if ttl is not None else 0
        return {
            "data_source_id": str(spec.data_source_id),
            "name": spec.name,
            "source": spec.source.model_dump(),
            "caching": {
                "enabled": spec.caching.enabled,
                "ttl": caching_ttl,
            },
        }

    async def publish_data_source(
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
        data_source = await self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=False
        )

        # Check if already published (idempotency)
        if data_source.is_published():
            return DataSourceSchema.from_orm(data_source)

        # Publish, validation is handled by DB constraints and schema validation
        data_source.status = DataSourceStatus.PUBLISHED
        await self.db.commit()

        self.logger.info("published_data_source", data_source_id=data_source_id)

        return DataSourceSchema.from_orm(data_source)


# Helper


async def _load_env_vars(db: AsyncSession, data_source_id: str) -> dict[str, str]:
    """
    Load environment variables from database.

    Args:
        db: Database session
        data_source_id: Data source UUID

    Returns:
        Dictionary of name -> value pairs
    """
    env_vars = {}
    env_var_stmt = select(DataSourceEnvVar).filter_by(data_source_id=data_source_id)
    env_var_result = await db.execute(env_var_stmt)
    all_vars = list(env_var_result.scalars().all())
    for var in all_vars:
        if var.value is None:
            value = ""
        elif isinstance(var.value, str):
            value = var.value
        else:
            value = str(var.value)
        env_vars[var.name] = value
    return env_vars


async def _load_credentials(db: AsyncSession, data_source_id: str) -> dict[str, str]:
    """
    Load authentication credentials from database.

    Args:
        db: Database session
        data_source_id: Data source UUID

    Returns:
        Dictionary of credential_type -> value pairs
    """
    cred_stmt = select(DataSourceCredential).filter_by(data_source_id=data_source_id)
    cred_result = await db.execute(cred_stmt)
    credentials_rows = list(cred_result.scalars().all())
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
