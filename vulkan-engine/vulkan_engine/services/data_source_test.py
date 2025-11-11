"""
Data source test service.

Handles execution and persistence of data source tests.
"""

import time
from urllib.parse import urlparse

import httpx
from jinja2 import TemplateSyntaxError, UndefinedError
from requests.exceptions import HTTPError as RequestsHTTPError
from vulkan.auth import AuthConfig

from vulkan_engine.db import (
    DataSourceTestResult,
)
from vulkan_engine.exceptions import (
    DataSourceNotFoundException,
    InvalidDataSourceException,
)
from vulkan_engine.loaders.data_source import DataSourceLoader
from vulkan_engine.logging import get_logger
from vulkan_engine.schemas import (
    DataSourceTestRequest,
    DataSourceTestRequestById,
    DataSourceTestResponse,
)
from vulkan_engine.services.base import BaseService
from vulkan_engine.services.data_source import (
    _load_credentials,
    _load_env_vars,
)
from vulkan_engine.services.request_preparation import (
    add_auth_headers,
    prepare_request_fields,
)


class DataSourceTestService(BaseService):
    """Service for testing data sources."""

    def __init__(self, db):
        """
        Initialize data source test service.

        Args:
            db: Database session
        """
        super().__init__(db)
        self.logger = get_logger(__name__)

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

    def _parse_response_data(self, response: httpx.Response) -> str | dict | list:
        """
        Parse HTTP response data with graceful fallback chain.

        Attempts to parse response in the following order:
        1. JSON (dict/list) - most common API response format
        2. Text - for HTML, plain text, or malformed JSON
        3. Binary indicator - for images, PDFs, etc.
        """
        try:
            return response.json()
        except ValueError:
            # Not valid JSON, try text
            pass

        try:
            return response.text
        except Exception:
            # Unable to decode as text, likely binary content
            return f"<Binary content, {len(response.content)} bytes>"

    def _extract_error_message(
        self, response_data: str | dict | list, status_code: int
    ) -> str:
        """
        Extract meaningful error message from failed HTTP responses.

        """
        if isinstance(response_data, dict):
            return (
                response_data.get("detail")
                or response_data.get("error")
                or f"HTTP {status_code}"
            )
        return f"HTTP {status_code}"

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

        env_vars = _load_env_vars(self.db, test_request.data_source_id)
        credentials = _load_credentials(self.db, test_request.data_source_id)

        if test_request.env_vars:
            env_vars.update(test_request.env_vars)

        full_request = DataSourceTestRequest(
            url=source_config.get("url", ""),
            method=source_config.get("method", "GET"),
            headers=source_config.get("headers"),
            body=source_config.get("body"),
            # Merge params: base + runtime overrides
            params={
                **(source_config.get("params") or {}),
                **(test_request.params or {}),
            },
            env_vars=env_vars,
        )

        # Execute using the standard test method, passing auth config, credentials, and data source ID
        return await self.execute_test(
            full_request,
            auth_config=source_config.get("auth"),
            auth_credentials=credentials,
            data_source_id=test_request.data_source_id,
        )

    async def execute_test(
        self,
        test_request: DataSourceTestRequest,
        auth_config: dict | None = None,
        auth_credentials: dict | None = None,
        data_source_id: str | None = None,
    ) -> DataSourceTestResponse:
        """
        Execute a data source test.

        Args:
            test_request: Test request configuration
            auth_config: Optional authentication configuration (from HTTPSource.auth)
            auth_credentials: Optional authentication credentials (CLIENT_ID, CLIENT_SECRET, etc.)
            data_source_id: Optional data source ID (for auth cache key)

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
        resolved_url = None
        resolved_headers = {}

        try:
            # Prepare request fields using shared utility
            config = {
                "url": test_request.url,
                "headers": test_request.headers,
                "params": test_request.params,
                "body": test_request.body,
            }

            prepared = prepare_request_fields(
                config=config,
                local_variables=local_vars,
                env_variables=env_vars,
                method=test_request.method,
                timeout=30,
            )

            # Add authentication headers if auth is configured
            if auth_config and data_source_id:
                credentials_to_use = auth_credentials or {}

                cache_available = hasattr(self, "cache") and self.cache is not None

                prepared = add_auth_headers(
                    prepared=prepared,
                    auth_config=AuthConfig(**auth_config),
                    data_source_id=data_source_id,
                    credentials=credentials_to_use,
                    cache=self.cache if cache_available else None,
                )

            resolved_url = prepared.url
            resolved_headers = prepared.headers

            async with httpx.AsyncClient(timeout=prepared.timeout) as client:
                response = await client.request(
                    method=prepared.method,
                    url=prepared.url,
                    headers=prepared.headers,
                    params=prepared.params,
                    json=prepared.body,
                )
                status_code = response.status_code
                response_headers = dict(response.headers)

                # Parse response data with proper fallback chain
                response_data = self._parse_response_data(response)

                # Extract error message for failed requests
                if status_code >= 400:
                    error = self._extract_error_message(response_data, status_code)

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
        except RequestsHTTPError as e:
            # HTTP error, used by auth handler
            if e.response is not None:
                status_code = e.response.status_code
                error = f"Authentication failed: {e.response.status_code} {e.response.reason}"
            else:
                status_code = 500
                error = f"Authentication failed: {str(e)}"
        except Exception as e:
            error = f"Unexpected error [{type(e).__name__}]: {str(e)}"
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

        self.logger.info(
            "data_source_test_executed",
            method=test_request.method,
            url=test_request.url,
            status_code=status_code,
            elapsed_ms=round(elapsed_ms, 2),
        )

        # Return response
        return DataSourceTestResponse(
            test_id=test_result.test_id,
            request_url=resolved_url,
            request_headers=resolved_headers,
            status_code=status_code,
            response_time_ms=elapsed_ms,
            response_body=response_data,
            response_headers=response_headers,
            error=error,
        )
