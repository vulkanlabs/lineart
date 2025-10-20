import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import jwt
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BaseAppClient(ABC):
    """Abstract base client for app server communication."""

    def __init__(self, server_url: str, run_id: str, project_id: str | None = None):
        self.server_url = server_url
        self.run_id = run_id
        self.project_id = project_id
        self.session = self._create_session()
        self._setup_auth()

    def _create_session(self) -> requests.Session:
        """Create session with fast retry logic for low latency."""
        session = requests.Session()

        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            # TODO: add jitter, consider adding 429
            status_forcelist=[502, 503, 504],  # Only retry on gateway errors
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    @abstractmethod
    def _setup_auth(self):
        """Configure session authentication headers."""
        pass

    def _request(
        self, method: str, endpoint: str, timeout: int = 10, **kwargs
    ) -> requests.Response:
        """
        Central request handler with logging and consistent error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint (will be appended to server_url)
            timeout: Request timeout in seconds (default: 10)
            **kwargs: Additional arguments passed to requests
        """
        url = f"{self.server_url}{endpoint}"
        log_context = {"run_id": self.run_id, "method": method, "endpoint": endpoint}
        logger.debug(f"{method} {endpoint}", extra=log_context)

        start_time = time.time()
        try:
            kwargs["timeout"] = timeout
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            elapsed = time.time() - start_time

            logger.debug(
                f"{method} {endpoint} -> {response.status_code} ({elapsed:.2f}s)",
                extra={
                    **log_context,
                    "status_code": response.status_code,
                    "elapsed_seconds": elapsed,
                },
            )

            return response

        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            error_msg = f"Request timeout after {elapsed:.2f}s"

            logger.error(
                f"{method} {endpoint} -> {error_msg}",
                extra={**log_context, "elapsed_seconds": elapsed},
            )
            raise requests.exceptions.RequestException(
                f"{error_msg} for {method} {endpoint}"
            ) from e

        except requests.exceptions.HTTPError as e:
            elapsed = time.time() - start_time
            status_code = (
                e.response.status_code if e.response is not None else "unknown"
            )
            response_text = e.response.text if e.response is not None else ""
            error_msg = f"HTTP {status_code}: {response_text}"

            logger.error(
                f"{method} {endpoint} -> {error_msg} (elapsed: {elapsed:.2f}s)",
                extra={
                    **log_context,
                    "elapsed_seconds": elapsed,
                    "status_code": status_code,
                    "response_text": response_text,
                },
            )
            raise requests.exceptions.RequestException(
                f"{error_msg} for {method} {endpoint}"
            ) from e

        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            error_msg = str(e)

            logger.error(
                f"{method} {endpoint} -> Request failed: {error_msg} (elapsed: {elapsed:.2f}s)",
                extra={
                    **log_context,
                    "elapsed_seconds": elapsed,
                    "error": error_msg,
                },
            )
            raise

    # Core API methods
    def fetch_data(
        self,
        data_source: str,
        configured_params: dict,
    ) -> requests.Response:
        """Fetch data from data broker."""
        return self._request(
            "POST",
            "/internal/data-broker",
            json={
                "run_id": self.run_id,
                "project_id": self.project_id,
                "data_source_name": data_source,
                "configured_params": configured_params,
            },
        )

    def run_version_sync(self, policy_version_id: str, data: dict) -> dict:
        """Create a new run for a policy version."""
        response = self._request(
            "POST",
            "/internal/run-version-sync",
            json={
                "policy_version_id": policy_version_id,
                "project_id": self.project_id,
                "input_data": data.get("input_data", {}),
                "config_variables": data.get("config_variables", {}),
            },
        )

        if response.status_code != 200:
            raise ValueError(
                f"Failed to create run for policy version {policy_version_id}: {response.text}"
            )

        result: dict = response.json()
        return {**result, "data": result.get("run_metadata", {})}

    def update_run_status(
        self,
        status: str,
        result: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update the status of the current run."""
        response = self._request(
            "PUT",
            f"/internal/runs/{self.run_id}",
            json={
                "project_id": self.project_id,
                "result": result,
                "status": status,
                "metadata": metadata,
            },
        )

        success = response.status_code in {200, 204}

        if not success:
            logger.error(
                f"Failed to update run status to {status}: {response.status_code}",
                extra={
                    "run_id": self.run_id,
                    "status": status,
                    "status_code": response.status_code,
                },
            )

        return success

    def publish_step_metadata(self, step_name: str, metadata: Dict[str, Any]) -> None:
        """Publish metadata for a specific step."""
        response = self._request(
            "POST",
            f"/internal/runs/{self.run_id}/metadata",
            json={
                "project_id": self.project_id,
                "step_name": step_name,
                **metadata,
            },
        )

        if response.status_code != 200:
            logger.error(
                f"Failed to publish metadata for step {step_name}: {response.status_code}",
                extra={
                    "run_id": self.run_id,
                    "step_name": step_name,
                    "status_code": response.status_code,
                },
            )
            raise ValueError(
                f"Failed to publish metadata for step {step_name}: {response.text}"
            )


class SimpleAppClient(BaseAppClient):
    """Basic client without authentication."""

    def _setup_auth(self):
        """No authentication setup needed."""
        logger.debug("Using simple client without authentication")


class JWTAppClient(BaseAppClient):
    """Client with JWT authentication (single token per run)."""

    def __init__(
        self,
        server_url: str,
        run_id: str,
        jwt_secret: str,
        jwt_issuer: str,
        jwt_audience: str,
        jwt_ttl: int = 3600,  # Default 1 hour for entire run
        project_id: str | None = None,
    ):
        self.jwt_secret = jwt_secret
        self.jwt_issuer = jwt_issuer
        self.jwt_audience = jwt_audience
        self.jwt_ttl = jwt_ttl
        super().__init__(server_url, run_id, project_id)

    def _setup_auth(self):
        """Generate JWT once and configure session with bearer token."""
        token = self._generate_jwt()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

        logger.debug(
            f"Using JWT client with issuer={self.jwt_issuer}, audience={self.jwt_audience}",
            extra={
                "run_id": self.run_id,
                "jwt_issuer": self.jwt_issuer,
                "jwt_audience": self.jwt_audience,
                "jwt_ttl": self.jwt_ttl,
            },
        )

    def _generate_jwt(self) -> str:
        """Generate JWT token for service-to-service auth (once per run)."""
        now = int(time.time())
        payload = {
            "iss": self.jwt_issuer,
            "aud": self.jwt_audience,
            "iat": now,
            "exp": now + self.jwt_ttl,
            "sub": f"run-{self.run_id}",
            "jti": self.run_id,
        }

        logger.debug(
            f"Generated JWT token valid for {self.jwt_ttl} seconds",
            extra={"run_id": self.run_id, "jwt_ttl": self.jwt_ttl},
        )

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")


def create_app_client(
    server_url: str, run_id: str, project_id: str | None = None
) -> BaseAppClient:
    """
    Factory function to create the appropriate client based on environment variables.

    Automatically detects JWT mode based on presence of required environment variables:
    - VULKAN_JWT_SECRET
    - VULKAN_JWT_ISSUER
    - VULKAN_JWT_AUDIENCE
    - VULKAN_JWT_TTL (optional, defaults to 3600)

    Args:
        server_url: The server URL
        run_id: The run identifier
        project_id: Optional project identifier

    Returns:
        JWTAppClient if all required JWT environment variables are set,
        SimpleAppClient if no JWT variables are set

    Raises:
        ValueError: If partial JWT configuration is detected
    """
    secret = os.getenv("VULKAN_JWT_SECRET")
    issuer = os.getenv("VULKAN_JWT_ISSUER")
    audience = os.getenv("VULKAN_JWT_AUDIENCE")
    ttl = int(os.getenv("VULKAN_JWT_TTL", "3600"))
    required = [secret, issuer, audience]

    if all(required):
        return JWTAppClient(
            run_id=run_id,
            project_id=project_id,
            server_url=server_url,
            jwt_secret=secret,
            jwt_issuer=issuer,
            jwt_audience=audience,
            jwt_ttl=ttl,
        )
    elif any(required):
        missing = []
        if not secret:
            missing.append("VULKAN_JWT_SECRET")
        if not issuer:
            missing.append("VULKAN_JWT_ISSUER")
        if not audience:
            missing.append("VULKAN_JWT_AUDIENCE")

        raise ValueError(
            f"Incomplete JWT configuration. Missing environment variables: {', '.join(missing)}. "
            "Either provide all JWT variables for authenticated mode, or none for simple mode."
        )
    else:
        return SimpleAppClient(
            run_id=run_id,
            project_id=project_id,
            server_url=server_url,
        )
