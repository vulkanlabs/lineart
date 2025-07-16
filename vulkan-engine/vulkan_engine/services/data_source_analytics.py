"""
Data source analytics and metrics service.

Handles all analytics operations related to data sources including usage statistics,
performance metrics, cache statistics, and response time analysis.
"""

import time
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import case, select
from sqlalchemy import func as F

from vulkan.spec.nodes import NodeType
from vulkan_engine.db import (
    DataObjectOrigin,
    Run,
    RunDataRequest,
    StepMetadata,
)
from vulkan_engine.loaders import DataSourceLoader
from vulkan_engine.services.base import BaseService
from vulkan_engine.utils import validate_date_range


class DataSourceAnalyticsService(BaseService):
    """Service for data source analytics and metrics."""

    def __init__(self, db, logger=None):
        """
        Initialize data source analytics service.

        Args:
            db: Database session
            logger: Optional logger
        """
        super().__init__(db, logger)
        self.data_source_loader = DataSourceLoader(db)

    def get_usage_statistics(
        self,
        data_source_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        project_id: str = None,
    ) -> dict[str, Any]:
        """
        Get usage statistics for a data source.

        Args:
            data_source_id: Data source UUID
            start_date: Start date filter
            end_date: End date filter
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with usage statistics
        """
        # Validate data source exists
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )

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
        project_id: str = None,
    ) -> dict[str, Any]:
        """
        Get performance metrics for a data source.

        Args:
            data_source_id: Data source UUID
            start_date: Start date filter
            end_date: End date filter
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with performance metrics
        """
        # Validate data source exists
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )

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
        project_id: str = None,
    ) -> dict[str, Any]:
        """
        Get cache statistics for a data source.

        Args:
            data_source_id: Data source UUID
            start_date: Start date filter
            end_date: End date filter
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with cache statistics
        """
        # Validate data source exists
        self.data_source_loader.get_data_source(
            data_source_id=data_source_id, project_id=project_id, include_archived=True
        )

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
