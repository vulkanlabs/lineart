"""
Authentication handler for DataSources.

Handles authentication for HTTP requests to external APIs:
- Basic Auth: Direct client_id:client_secret encoding
- Bearer/OAuth: Token exchange with Redis caching
"""

import base64
from typing import Dict

import redis
import requests

from vulkan.auth import Auth, AuthMethod


class AuthHandler:
    """
    Handles authentication for DataSources.

    Supports two authentication methods:
    1. Basic Auth: Encodes client_id:client_secret in Base64
    2. Bearer/OAuth: Exchanges credentials for access token with caching

    Usage:
        auth_handler = AuthHandler(
            auth_config=datasource.auth,
            data_source_id=datasource.id,
            env_variables={"CLIENT_ID": "...", "CLIENT_SECRET": "..."},
            cache=redis_client
        )

        headers = auth_handler.get_auth_headers()
        # {"Authorization": "Basic ..." or "Bearer ..."}
    """

    def __init__(
        self,
        auth_config: Auth,
        data_source_id: str,
        env_variables: dict,
        cache: redis.Redis | None = None,
    ):
        """
        Args:
            auth_config: Authentication configuration (from DataSource.source.auth)
            data_source_id: DataSource ID (used for cache key)
            env_variables: Environment variables including CLIENT_ID and CLIENT_SECRET
            cache: Redis client for token caching (optional, required for Bearer)
        """
        self.auth_config = auth_config
        self.data_source_id = data_source_id
        self.env_variables = env_variables
        self.cache = cache

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Generates authentication headers based on auth method.

        Returns:
            Dictionary with Authorization header

        Examples:
            Basic Auth:
                {"Authorization": "Basic bXktY2xpZW50LWlkLTEyMzpzZWNyZXQteHl6"}

            Bearer Auth:
                {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIs..."}
        """
        if self.auth_config.method == AuthMethod.BASIC:
            return self._handle_basic()

        if self.auth_config.method == AuthMethod.BEARER:
            return self._handle_bearer()

        return {}

    def _handle_basic(self) -> Dict[str, str]:
        """
        Handles Basic authentication.

        Process:
        1. Get CLIENT_ID and CLIENT_SECRET from env variables
        2. Concatenate as "client_id:client_secret"
        3. Base64 encode
        4. Return Authorization header

        Returns:
            {"Authorization": "Basic <base64(client_id:client_secret)>"}
        """
        client_id = self.env_variables.get("CLIENT_ID", "")
        client_secret = self.env_variables.get("CLIENT_SECRET", "")

        credentials = f"{client_id}:{client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        return {"Authorization": f"Basic {encoded}"}

    def _handle_bearer(self) -> Dict[str, str]:
        """
        Handles Bearer/OAuth authentication with token caching.

        Flow:
        1. Check Redis for cached token
        2. If found and not expired: Return cached token
        3. If not found or expired: Fetch new token from API
        4. Cache new token with TTL
        5. Return Bearer header

        Returns:
            {"Authorization": "Bearer <access_token>"}

        Raises:
            requests.HTTPError: If token request fails
        """
        # Redis cache key (unique per DataSource)
        cache_key = f"auth_token:{self.data_source_id}"

        # Check cache if available
        if self.cache:
            cached_token = self.cache.get(cache_key)
            if cached_token:
                token = cached_token.decode("utf-8")
                return {"Authorization": f"Bearer {token}"}

        access_token = self._fetch_token()
        return {"Authorization": f"Bearer {access_token}"}

    def _fetch_token(self) -> str:
        """
        Fetches a new access token from OAuth token endpoint

        Process:
        1. Create Basic auth header (client_id:client_secret)
        2. POST to token_url with grant_type and scope
        3. Parse access_token and expires_in from response
        4. Cache token in Redis with TTL
        5. Return access_token

        Returns:
            access_token string

        Raises:
            requests.HTTPError: If token request fails
            KeyError: If response doesn't contain access_token
        """
        client_id = self.env_variables.get("CLIENT_ID", "")
        client_secret = self.env_variables.get("CLIENT_SECRET", "")

        credentials = f"{client_id}:{client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        body = {
            "grant_type": self.auth_config.grant_type.value,
        }

        if self.auth_config.scope:
            body["scope"] = self.auth_config.scope

        if self.auth_config.grant_type.value == "password":
            username = self.env_variables.get("USERNAME", "")
            password = self.env_variables.get("PASSWORD", "")
            if username:
                body["username"] = username
            if password:
                body["password"] = password

        response = requests.post(
            url=self.auth_config.token_url,
            headers={"Authorization": f"Basic {encoded}"},
            data=body,
            timeout=10,
        )

        response.raise_for_status()

        token_data = response.json()
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)  # 1 hour

        # Cache token with TTL
        if self.cache:
            ttl = max(
                expires_in - 60, 60
            )  # subtract 60s buffer to refresh before expiry
            cache_key = f"auth_token:{self.data_source_id}"
            self.cache.setex(cache_key, ttl, access_token)

        return access_token
