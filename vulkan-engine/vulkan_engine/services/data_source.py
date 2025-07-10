"""
Data source and data broker management service.

Handles all business logic related to data sources including CRUD operations,
environment variables, data objects, usage statistics, and data broker operations.
"""

import time
from datetime import date
from typing import Any

import pandas as pd
import requests
from sqlalchemy import case, select
from sqlalchemy import func as F

from vulkan.data_source import DataSourceType
from vulkan.schemas import DataSourceSpec
from vulkan.spec.nodes import NodeType
from vulkan_engine.data.broker import DataBroker
from vulkan_engine.db import (
    DataObject,
    DataObjectOrigin,
    DataSource,
    DataSourceEnvVar,
    PolicyDataDependency,
    PolicyVersion,
    Run,
    RunDataRequest,
    StepMetadata,
    UploadedFile,
)
from vulkan_engine.exceptions import (
    DataBrokerException,
    DataBrokerRequestException,
    DataSourceAlreadyExistsException,
    DataSourceNotFoundException,
    InvalidDataSourceException,
)
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
from vulkan_engine.utils import validate_date_range


class DataSourceService(BaseService):
    """Service for managing data sources and data operations."""

    def list_data_sources(self, include_archived: bool = False) -> list[DataSource]:
        """
        List all data sources.

        Args:
            include_archived: Whether to include archived data sources

        Returns:
            List of DataSource objects
        """
        filters = {}
        if not include_archived:
            filters["archived"] = False

        stmt = select(DataSource).filter_by(**filters)
        return self.db.execute(stmt).scalars().all()

    def create_data_source(self, spec: DataSourceSpec) -> dict[str, str]:
        """
        Create a new data source.

        Args:
            spec: Data source specification

        Returns:
            Dictionary with data_source_id

        Raises:
            DataSourceAlreadyExistsException: If data source name already exists
            InvalidDataSourceException: If data source configuration is invalid
        """
        # Check if data source already exists
        existing = self.db.query(DataSource).filter_by(name=spec.name).first()
        if existing:
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
        self.db.add(data_source)
        self.db.commit()

        return {"data_source_id": data_source.data_source_id}

    def get_data_source(self, data_source_id: str) -> DataSource:
        """
        Get a data source by ID.

        Args:
            data_source_id: Data source UUID

        Returns:
            DataSource object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        data_source = (
            self.db.query(DataSource).filter_by(data_source_id=data_source_id).first()
        )

        if not data_source:
            raise DataSourceNotFoundException("Data source not found")

        return data_source

    def delete_data_source(self, data_source_id: str) -> dict[str, str]:
        """
        Delete (archive) a data source.

        Args:
            data_source_id: Data source UUID

        Returns:
            Dictionary with data_source_id

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If data source is in use
        """
        data_source = (
            self.db.query(DataSource)
            .filter_by(data_source_id=data_source_id, archived=False)
            .first()
        )

        if not data_source:
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
        self, data_source_id: str, desired_variables: list[DataSourceEnvVarBase]
    ) -> dict[str, Any]:
        """
        Set environment variables for a data source.

        Args:
            data_source_id: Data source UUID
            desired_variables: List of environment variables to set

        Returns:
            Dictionary with data_source_id and variables

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If variables are not supported
        """
        data_source = (
            self.db.query(DataSource)
            .filter_by(data_source_id=data_source_id, archived=False)
            .first()
        )

        if not data_source:
            raise DataSourceNotFoundException("Data source not found")

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
        self, data_source_id: str
    ) -> list[DataSourceEnvVarSchema]:
        """
        Get environment variables for a data source.

        Args:
            data_source_id: Data source UUID

        Returns:
            List of DataSourceEnvVar objects

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        data_source = (
            self.db.query(DataSource)
            .filter_by(data_source_id=data_source_id, archived=False)
            .first()
        )

        if not data_source:
            raise DataSourceNotFoundException("Data source not found")

        return (
            self.db.query(DataSourceEnvVar)
            .filter_by(data_source_id=data_source_id)
            .all()
        )

    def list_data_objects(self, data_source_id: str) -> list[DataObjectMetadata]:
        """
        List data objects for a data source.

        Args:
            data_source_id: Data source UUID

        Returns:
            List of DataObjectMetadata objects

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
        """
        data_source = (
            self.db.query(DataSource).filter_by(data_source_id=data_source_id).first()
        )

        if not data_source:
            raise DataSourceNotFoundException("Data source not found")

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

    def get_data_object(self, data_source_id: str, data_object_id: str) -> DataObject:
        """
        Get a specific data object.

        Args:
            data_source_id: Data source UUID
            data_object_id: Data object UUID

        Returns:
            DataObject object

        Raises:
            DataSourceNotFoundException: If data object doesn't exist
        """
        data_object = (
            self.db.query(DataObject)
            .filter_by(data_source_id=data_source_id, data_object_id=data_object_id)
            .first()
        )

        if not data_object:
            raise DataSourceNotFoundException("Data object not found")

        return data_object

    def get_usage_statistics(
        self,
        data_source_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Get usage statistics for a data source.

        Args:
            data_source_id: Data source UUID
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Dictionary with usage statistics
        """
        start_date, end_date = validate_date_range(start_date, end_date)
        date_clause = F.DATE(RunDataRequest.created_at).label("date")

        query = (
            select(
                date_clause,
                F.count(RunDataRequest.run_data_request_id).label("count"),
            )
            .where(
                (RunDataRequest.data_source_id == data_source_id)
                & (RunDataRequest.created_at >= start_date)
                & (F.DATE(RunDataRequest.created_at) <= end_date)
            )
            .group_by(date_clause)
        )

        df = pd.read_sql(query, self.db.bind).fillna(0).sort_values("date")
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df["value"] = df["count"].astype(int)

        return {"requests_by_date": df.to_dict(orient="records")}

    def get_performance_metrics(
        self,
        data_source_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Get performance metrics for a data source.

        Args:
            data_source_id: Data source UUID
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Dictionary with performance metrics
        """
        start_date, end_date = validate_date_range(start_date, end_date)

        # Get data for response time and error metrics from StepMetadata
        # TODO: this query is not optimal, and it should be a point of attention.
        # Key things of note:
        # 1. There aren't any indices on the created_at column of StepMetadata
        # 2. The run_id columns are also not indexed in all tables
        # 3. It might be worth considering using a materialized view for this query
        metrics_query = (
            select(
                F.DATE(StepMetadata.created_at).label("date"),
                F.avg((StepMetadata.end_time - StepMetadata.start_time)).label(
                    "avg_duration_ms"
                ),
                F.avg(
                    case(
                        {True: 0.0, False: 1.0},
                        value=StepMetadata.error.is_(None),
                        else_=0.0,
                    )
                ).label("error_rate"),
            )
            .where(
                (StepMetadata.created_at >= start_date)
                & (F.DATE(StepMetadata.created_at) <= end_date)
                & (StepMetadata.node_type == NodeType.DATA_INPUT.value)
                & (RunDataRequest.data_source_id == data_source_id)
            )
            .join(Run, Run.run_id == StepMetadata.run_id)
            .join(RunDataRequest, RunDataRequest.run_id == Run.run_id)
            .group_by(F.DATE(StepMetadata.created_at))
            .order_by(F.DATE(StepMetadata.created_at))
        )

        sql_start = time.time()
        metrics_df = pd.read_sql(metrics_query, self.db.bind)
        sql_time = time.time() - sql_start

        if self.logger:
            self.logger.system.debug(
                f"data-source/metrics: Query completed in {sql_time:.3f}s, "
                f"retrieved {len(metrics_df)} rows"
            )

        # Process and format the results
        processing_start = time.time()
        if not metrics_df.empty:
            # Format date for consistency and round values
            metrics_df["date"] = pd.to_datetime(metrics_df["date"]).dt.strftime(
                "%Y-%m-%d"
            )
            metrics_df["avg_duration_ms"] = metrics_df["avg_duration_ms"].round(2)
            metrics_df["error_rate"] = (metrics_df["error_rate"] * 100).round(2)

            # Split into separate dataframes for the API response
            avg_response_time = metrics_df[["date", "avg_duration_ms"]].rename(
                columns={"avg_duration_ms": "value"}
            )
            error_rate = metrics_df[["date", "error_rate"]].rename(
                columns={"error_rate": "value"}
            )
        else:
            avg_response_time = pd.DataFrame(columns=["date", "value"])
            error_rate = pd.DataFrame(columns=["date", "value"])

        processing_time = time.time() - processing_start
        if self.logger:
            self.logger.system.debug(
                f"data-source/metrics: DataFrame processing completed in {processing_time:.3f}s"
            )

        return {
            "avg_response_time_by_date": avg_response_time.to_dict(orient="records"),
            "error_rate_by_date": error_rate.to_dict(orient="records"),
        }

    def get_cache_statistics(
        self,
        data_source_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Get cache statistics for a data source.

        Args:
            data_source_id: Data source UUID
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Dictionary with cache statistics
        """
        start_date, end_date = validate_date_range(start_date, end_date)
        date_clause = F.DATE(RunDataRequest.created_at).label("date")

        cache_query = (
            select(
                date_clause,
                RunDataRequest.data_origin,
                F.count(RunDataRequest.run_data_request_id).label("count"),
            )
            .where(
                (RunDataRequest.data_source_id == data_source_id)
                & (RunDataRequest.created_at >= start_date)
                & (F.DATE(RunDataRequest.created_at) <= end_date)
            )
            .group_by(date_clause, RunDataRequest.data_origin)
        )

        cache_df = pd.read_sql(cache_query, self.db.bind)
        cache_df["data_origin"] = cache_df["data_origin"].map(
            {
                DataObjectOrigin.CACHE: DataObjectOrigin.CACHE.value,
                DataObjectOrigin.REQUEST: DataObjectOrigin.REQUEST.value,
            }
        )

        # Calculate cache hit ratio by date
        if not cache_df.empty:
            # Pivot the data to get CACHE and SOURCE as separate columns
            cache_pivot = (
                cache_df.pivot(index="date", columns="data_origin", values="count")
                .fillna(0)
                .reset_index()
            )

            # Make sure we have both CACHE and REQUEST columns
            if DataObjectOrigin.CACHE.value not in cache_pivot.columns:
                cache_pivot[DataObjectOrigin.CACHE.value] = 0
            if DataObjectOrigin.REQUEST.value not in cache_pivot.columns:
                cache_pivot[DataObjectOrigin.REQUEST.value] = 0

            # Calculate hit ratio
            cache_pivot["total"] = (
                cache_pivot[DataObjectOrigin.CACHE.value]
                + cache_pivot[DataObjectOrigin.REQUEST.value]
            )
            cache_pivot["hit_ratio"] = (
                (cache_pivot[DataObjectOrigin.CACHE.value] / cache_pivot["total"]) * 100
            ).round(2)

            # Handle division by zero
            cache_pivot["hit_ratio"] = cache_pivot["hit_ratio"].fillna(0)

            # Format the result
            result = cache_pivot[["date", "hit_ratio"]].rename(
                columns={"hit_ratio": "value"}
            )
            result["date"] = pd.to_datetime(result["date"]).dt.strftime("%Y-%m-%d")
        else:
            result = pd.DataFrame(columns=["date", "value"])

        return {"cache_hit_ratio_by_date": result.to_dict(orient="records")}

    def request_data_from_broker(
        self, request: DataBrokerRequest
    ) -> DataBrokerResponse:
        """
        Request data through the data broker.

        Args:
            request: Data broker request

        Returns:
            DataBrokerResponse object

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If environment variables missing
        """
        # Find data source
        data_source = (
            self.db.query(DataSource).filter_by(name=request.data_source_name).first()
        )
        if not data_source:
            raise DataSourceNotFoundException("Data source not found")

        # Create data source spec
        spec = DataSourceSchema.from_orm(data_source)

        # Initialize broker
        broker = DataBroker(self.db, self.logger.system if self.logger else None, spec)

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
