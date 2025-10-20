"""
Data source test service.

Handles execution and persistence of data source tests.
"""

import time
from urllib.parse import urlparse

import httpx
from jinja2 import TemplateSyntaxError, UndefinedError

from vulkan.node_config import configure_fields, resolve_template
from vulkan_engine.db import DataSourceTestResult
from vulkan_engine.exceptions import (
    DataSourceNotFoundException,
    InvalidDataSourceException,
)
from vulkan_engine.loaders.data_source import DataSourceLoader
from vulkan_engine.schemas import (
    DataSourceTestRequest,
    DataSourceTestRequestById,
    DataSourceTestResponse,
)
from vulkan_engine.services.base import BaseService


class DataSourceTestService(BaseService):
    """Service for testing data sources."""

    def __init__(self, db, logger=None):
        """
        Initialize data source test service.

        Args:
            db: Database session
            logger: Optional logger
        """
        super().__init__(db, logger)

    def _validate_test_request(self, test_request: DataSourceTestRequest) -> None:
        """
        Validate test request configuration.

        Args:
            test_request: Test request to validate

        Raises:
            InvalidDataSourceException: If request is invalid
        """
        # Validate URL scheme
        try:
            parsed = urlparse(test_request.url)
            if parsed.scheme not in ["http", "https"]:
                raise InvalidDataSourceException(
                    f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed"
                )
        except Exception as e:
            if isinstance(e, InvalidDataSourceException):
                raise
            raise InvalidDataSourceException(f"Invalid URL format: {str(e)}")

        # Validate body size (1MB limit)
        if test_request.body:
            body_size = len(str(test_request.body))
            if body_size > 1_000_000:
                raise InvalidDataSourceException(
                    f"Request body too large: {body_size} bytes (max 1MB)"
                )

    async def execute_test_by_id(
        self, test_request: DataSourceTestRequestById
    ) -> DataSourceTestResponse:
        """
        Execute a data source test for an existing data source by ID.

        Fetches the data source configuration and merges with runtime parameters
        and environment variables before executing the test.

        Args:
            test_request: Simplified test request with data_source_id and runtime overrides

        Returns:
            DataSourceTestResponse with test results

        Raises:
            DataSourceNotFoundException: If data source doesn't exist
            InvalidDataSourceException: If request or configuration is invalid
        """
        # Load data source configuration
        loader = DataSourceLoader(self.db)
        try:
            data_source = loader.get_data_source(
                test_request.data_source_id, include_archived=True
            )
        except DataSourceNotFoundException:
            raise DataSourceNotFoundException(
                f"Data source {test_request.data_source_id} not found"
            )

        # Build full test request by merging data source config with runtime params
        source_config = data_source.source
        full_request = DataSourceTestRequest(
            url=source_config.get("url", ""),
            method=source_config.get("method", "GET"),
            headers=source_config.get("headers"),
            body=source_config.get("body"),
            # Merge params: data source base + runtime overrides
            params={
                **(source_config.get("params") or {}),
                **(test_request.params or {}),
            },
            # Use provided env_vars for template resolution
            env_vars=test_request.env_vars,
        )

        # Execute using the standard test method
        return await self.execute_test(full_request)

    async def execute_test(
        self, test_request: DataSourceTestRequest
    ) -> DataSourceTestResponse:
        """
        Execute a data source test.

        Args:
            test_request: Test request configuration

        Returns:
            DataSourceTestResponse with test results

        Raises:
            InvalidDataSourceException: If request is invalid
        """
        # Validate request before execution
        self._validate_test_request(test_request)

        # Get env vars and configured params for template resolution
        env_vars = test_request.env_vars or {}
        local_vars = test_request.params or {}

        # Prepare request data for audit
        request_data = {
            "url": test_request.url,
            "method": test_request.method,
            "headers": test_request.headers,
            "params": test_request.params,
            "body": test_request.body,
            "env_vars": {k: "***" for k in env_vars.keys()},  # Sanitize
        }

        # Execute HTTP request with resolved templates
        start_time = time.perf_counter()
        response_data = None
        error = None
        status_code = None
        response_headers = {}

        try:
            # Resolve URL template
            url = resolve_template(test_request.url, local_vars, env_vars)

            # Resolve template fields
            headers = configure_fields(test_request.headers or {}, local_vars, env_vars)
            params = configure_fields(test_request.params or {}, local_vars, env_vars)
            body = (
                configure_fields(test_request.body or {}, local_vars, env_vars)
                if test_request.body
                else None
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=test_request.method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body if body else None,
                )
                status_code = response.status_code
                response_headers = dict(response.headers)

                # Try to parse as JSON, fallback to text
                try:
                    response_data = response.json()
                except Exception:
                    response_data = response.text

        except (TemplateSyntaxError, UndefinedError) as e:
            error = f"Template resolution error: {str(e)}"
            status_code = 400
        except httpx.TimeoutException:
            error = "Request timed out after 30 seconds"
            status_code = 408
        except httpx.RequestError as e:
            error = f"Request failed: {str(e)}"
            status_code = 500
        except ValueError as e:
            error = f"Configuration error: {str(e)}"
            status_code = 400
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            status_code = 500

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Prepare response data for persistence
        response_payload = {
            "status_code": status_code,
            "response_time_ms": elapsed_ms,
            "response_body": response_data,
            "response_headers": response_headers,
            "error": error,
        }

        # Persist test result in background (inline persistence)
        test_result = DataSourceTestResult(
            request=request_data,
            response=response_payload,
        )
        self.db.add(test_result)
        self.db.commit()

        if self.logger:
            self.logger.system.info(
                f"Data source test executed: {test_request.method} {test_request.url} - "
                f"Status: {status_code}, Time: {elapsed_ms:.2f}ms"
            )

        # Return response
        return DataSourceTestResponse(
            test_id=test_result.test_id,
            status_code=status_code,
            response_time_ms=elapsed_ms,
            response_body=response_data,
            response_headers=response_headers,
            error=error,
        )
