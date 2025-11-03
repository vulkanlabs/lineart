"""
Data source test service.

Handles execution and persistence of data source tests.
"""

import time
from urllib.parse import urlparse

import httpx
from jinja2 import TemplateSyntaxError, UndefinedError
from requests.exceptions import HTTPError as RequestsHTTPError

from vulkan.auth import Auth
from vulkan.node_config import configure_fields, normalize_mapping, resolve_template
from vulkan_engine.db import DataSourceEnvVar, DataSourceTestResult
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
from vulkan_engine.services.auth_handler import AuthHandler
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

    def _load_all_env_vars(self, data_source_id: str) -> dict[str, str]:
        """
        Load all environment variables from database.

        Returns:
            Dictionary with all environment variable name-value pairs
        """
        env_vars = {}

        all_vars = (
            self.db.query(DataSourceEnvVar)
            .filter_by(data_source_id=data_source_id)
            .all()
        )

        for var in all_vars:
            if var.value is None:
                value = ""
            elif isinstance(var.value, str):
                value = var.value
            else:
                value = str(var.value)

            env_vars[var.name] = value

        return env_vars

    def _load_auth_credentials(self, data_source_id: str) -> dict[str, str]:
        """
        Load authentication credentials from database.

        Returns:
            Dictionary with CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD
        """
        env_vars = {}

        credentials = (
            self.db.query(DataSourceEnvVar)
            .filter_by(data_source_id=data_source_id)
            .filter(
                DataSourceEnvVar.name.in_(
                    ["CLIENT_ID", "CLIENT_SECRET", "USERNAME", "PASSWORD"]
                )
            )
            .all()
        )

        for credential in credentials:
            if credential.value is None:
                value = ""
            elif isinstance(credential.value, str):
                value = credential.value
            else:
                value = str(credential.value)

            env_vars[credential.name] = value

        return env_vars

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

        # Normalize headers and params from ConfigurableDict to template strings
        headers_normalized = normalize_mapping(source_config.get("headers"))
        params_base_normalized = normalize_mapping(source_config.get("params"))

        env_vars = self._load_all_env_vars(test_request.data_source_id)

        if test_request.env_vars:
            env_vars.update(test_request.env_vars)

        full_request = DataSourceTestRequest(
            url=source_config.get("url", ""),
            method=source_config.get("method", "GET"),
            headers=headers_normalized,
            body=source_config.get("body"),
            # Merge params: normalized base + runtime overrides
            params={
                **(params_base_normalized or {}),
                **(test_request.params or {}),
            },
            # Use merged env_vars
            env_vars=env_vars,
        )

        # Execute using the standard test method, passing auth config and data source ID
        return await self.execute_test(
            full_request,
            auth_config=source_config.get("auth"),
            data_source_id=test_request.data_source_id,
        )

    async def execute_test(
        self,
        test_request: DataSourceTestRequest,
        auth_config: dict | None = None,
        data_source_id: str | None = None,
    ) -> DataSourceTestResponse:
        """
        Execute a data source test.

        Args:
            test_request: Test request configuration
            auth_config: Optional authentication configuration (from HTTPSource.auth)
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
            # Resolve templates
            url = resolve_template(test_request.url, local_vars, env_vars)
            resolved_url = url

            headers = configure_fields(test_request.headers or {}, local_vars, env_vars)
            params = configure_fields(test_request.params or {}, local_vars, env_vars)
            body = (
                configure_fields(test_request.body, local_vars, env_vars)
                if test_request.body
                else None
            )
            resolved_headers = headers

            # Add authentication headers if auth is configured
            if auth_config and data_source_id:
                auth_obj = Auth(**auth_config)
                cache_available = hasattr(self, "cache") and self.cache is not None

                auth_handler = AuthHandler(
                    auth_config=auth_obj,
                    data_source_id=data_source_id,
                    env_variables=env_vars,
                    cache=self.cache if cache_available else None,
                )

                auth_headers = auth_handler.get_auth_headers()
                headers = {**headers, **auth_headers}
                resolved_headers = headers

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

        if self.logger:
            self.logger.system.info(
                f"Data source test executed: {test_request.method} {test_request.url} - "
                f"Status: {status_code}, Time: {elapsed_ms:.2f}ms"
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
