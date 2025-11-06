"""
Tests for authentication handler.

Tests the AuthHandler class for Basic and Bearer/OAuth2 authentication.
"""

import base64
from unittest.mock import Mock, patch

import pytest
from vulkan.auth import AuthConfig, AuthMethod, GrantType
from vulkan_engine.services.auth_handler import AuthHandler


class TestAuthHandlerBasic:
    """Test cases for Basic authentication."""

    @pytest.fixture
    def basic_auth_config(self):
        """Create a Basic auth configuration."""
        return AuthConfig(method=AuthMethod.BASIC)

    @pytest.fixture
    def credentials(self):
        """Create authentication credentials."""
        return {"CLIENT_ID": "test_user", "CLIENT_SECRET": "test_password"}

    @pytest.fixture
    def auth_handler(self, basic_auth_config, credentials):
        """Create an AuthHandler for Basic auth."""
        return AuthHandler(
            auth_config=basic_auth_config,
            data_source_id="test-ds-id",
            credentials=credentials,
            cache=None,
        )

    def test_basic_auth_generates_correct_header(self, auth_handler):
        """Test that Basic auth generates correct Authorization header."""
        headers = auth_handler.get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

        # Decode and verify credentials
        encoded_creds = headers["Authorization"].replace("Basic ", "")
        decoded = base64.b64decode(encoded_creds).decode()
        assert decoded == "test_user:test_password"

    def test_basic_auth_missing_client_id(self, basic_auth_config):
        """Test that missing CLIENT_ID results in empty credential in header."""
        handler = AuthHandler(
            auth_config=basic_auth_config,
            data_source_id="test-ds-id",
            credentials={"CLIENT_SECRET": "password"},
            cache=None,
        )

        headers = handler.get_auth_headers()

        # Should still generate header, but with empty client_id
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

        # Decode and verify: ":password" (empty client_id)
        encoded_creds = headers["Authorization"].replace("Basic ", "")
        decoded = base64.b64decode(encoded_creds).decode()
        assert decoded == ":password"

    def test_basic_auth_missing_client_secret(self, basic_auth_config):
        """Test that missing CLIENT_SECRET results in empty secret in header."""
        handler = AuthHandler(
            auth_config=basic_auth_config,
            data_source_id="test-ds-id",
            credentials={"CLIENT_ID": "user"},
            cache=None,
        )

        headers = handler.get_auth_headers()

        # Should still generate header, but with empty client_secret
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

        # Decode and verify: "user:" (empty client_secret)
        encoded_creds = headers["Authorization"].replace("Basic ", "")
        decoded = base64.b64decode(encoded_creds).decode()
        assert decoded == "user:"

    def test_basic_auth_with_special_characters(self, basic_auth_config):
        """Test Basic auth with special characters in credentials."""
        handler = AuthHandler(
            auth_config=basic_auth_config,
            data_source_id="test-ds-id",
            credentials={
                "CLIENT_ID": "user@example.com",
                "CLIENT_SECRET": "p@ssw0rd!#$%",
            },
            cache=None,
        )

        headers = handler.get_auth_headers()
        encoded_creds = headers["Authorization"].replace("Basic ", "")
        decoded = base64.b64decode(encoded_creds).decode()
        assert decoded == "user@example.com:p@ssw0rd!#$%"


class TestAuthHandlerBearer:
    """Test cases for Bearer/OAuth2 authentication."""

    @pytest.fixture
    def bearer_auth_config(self):
        """Create a Bearer auth configuration."""
        return AuthConfig(
            method=AuthMethod.BEARER,
            token_url="https://auth.example.com/token",
            grant_type=GrantType.CLIENT_CREDENTIALS,
            scope="read write",
        )

    @pytest.fixture
    def credentials(self):
        """Create authentication credentials."""
        return {"CLIENT_ID": "test_client", "CLIENT_SECRET": "test_secret"}

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        return redis_mock

    @pytest.fixture
    def auth_handler(self, bearer_auth_config, credentials, mock_redis):
        """Create an AuthHandler for Bearer auth."""
        return AuthHandler(
            auth_config=bearer_auth_config,
            data_source_id="test-ds-id",
            credentials=credentials,
            cache=mock_redis,
        )

    def test_bearer_auth_with_cached_token(self, auth_handler, mock_redis):
        """Test that Bearer auth uses cached token when available."""
        mock_redis.get.return_value = b"cached_access_token"

        headers = auth_handler.get_auth_headers()

        assert headers["Authorization"] == "Bearer cached_access_token"
        mock_redis.get.assert_called_once_with("auth_token:test-ds-id")

    @patch("requests.post")
    def test_bearer_auth_fetches_new_token(self, mock_post, auth_handler, mock_redis):
        """Test that Bearer auth fetches new token when cache is empty."""
        mock_redis.get.return_value = None
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        headers = auth_handler.get_auth_headers()

        assert headers["Authorization"] == "Bearer new_access_token"

        # Verify token was fetched with correct parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify URL
        assert call_args[1]["url"] == "https://auth.example.com/token"

        # Verify Authorization header (Basic auth with client credentials)
        assert "Authorization" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Authorization"].startswith("Basic ")

        # Verify body contains grant_type and scope
        assert call_args[1]["data"]["grant_type"] == "client_credentials"
        assert call_args[1]["data"]["scope"] == "read write"

    @patch("requests.post")
    def test_bearer_auth_caches_token(self, mock_post, auth_handler, mock_redis):
        """Test that Bearer auth caches fetched token."""
        mock_redis.get.return_value = None
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        auth_handler.get_auth_headers()

        # Verify token was cached with TTL
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[0] == "auth_token:test-ds-id"
        assert call_args[1] == 3540  # expires_in - 60 seconds buffer
        assert call_args[2] == "new_token"

    @patch("requests.post")
    def test_bearer_auth_missing_client_id(
        self, mock_post, bearer_auth_config, mock_redis
    ):
        """Test that missing CLIENT_ID results in empty credential in token request."""
        mock_redis.get.return_value = None
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        handler = AuthHandler(
            auth_config=bearer_auth_config,
            data_source_id="test-ds-id",
            credentials={"CLIENT_SECRET": "secret"},
            cache=mock_redis,
        )

        headers = handler.get_auth_headers()

        # Should still make request, but with empty client_id
        assert "Authorization" in headers
        mock_post.assert_called_once()

        # Verify Authorization header has empty client_id (":secret")
        call_args = mock_post.call_args
        auth_header = call_args[1]["headers"]["Authorization"]
        encoded = auth_header.replace("Basic ", "")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == ":secret"

    @patch("requests.post")
    def test_bearer_auth_missing_client_secret(
        self, mock_post, bearer_auth_config, mock_redis
    ):
        """Test that missing CLIENT_SECRET results in empty secret in token request."""
        mock_redis.get.return_value = None
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        handler = AuthHandler(
            auth_config=bearer_auth_config,
            data_source_id="test-ds-id",
            credentials={"CLIENT_ID": "client"},
            cache=mock_redis,
        )

        headers = handler.get_auth_headers()

        # Should still make request, but with empty client_secret
        assert "Authorization" in headers
        mock_post.assert_called_once()

        # Verify Authorization header has empty client_secret ("client:")
        call_args = mock_post.call_args
        auth_header = call_args[1]["headers"]["Authorization"]
        encoded = auth_header.replace("Basic ", "")
        decoded = base64.b64decode(encoded).decode()
        assert decoded == "client:"

    @patch("requests.post")
    def test_bearer_auth_token_fetch_failure(self, mock_post, auth_handler, mock_redis):
        """Test that token fetch failure raises appropriate error."""
        mock_redis.get.return_value = None
        mock_post.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            auth_handler.get_auth_headers()

    @patch("requests.post")
    def test_bearer_auth_different_grant_types(self, mock_post, mock_redis):
        """Test Bearer auth with different grant types."""
        grant_type_configs = [
            (
                GrantType.CLIENT_CREDENTIALS,
                {"CLIENT_ID": "test_client", "CLIENT_SECRET": "test_secret"},
            ),
            (GrantType.PASSWORD, {"USERNAME": "test_user", "PASSWORD": "test_pass"}),
            (GrantType.IMPLICIT, {}),
        ]

        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "token", "expires_in": 3600}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        for grant_type, creds in grant_type_configs:
            auth_config = AuthConfig(
                method=AuthMethod.BEARER,
                token_url="https://auth.example.com/token",
                grant_type=grant_type,
                scope="read",
            )
            handler = AuthHandler(
                auth_config=auth_config,
                data_source_id="test-ds-id",
                credentials=creds,
                cache=mock_redis,
            )

            headers = handler.get_auth_headers()
            assert "Authorization" in headers

    def test_bearer_auth_without_cache(self, bearer_auth_config, credentials):
        """Test Bearer auth works without Redis cache."""
        handler = AuthHandler(
            auth_config=bearer_auth_config,
            data_source_id="test-ds-id",
            credentials=credentials,
            cache=None,
        )

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "token",
                "expires_in": 3600,
            }
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            headers = handler.get_auth_headers()

            assert headers["Authorization"] == "Bearer token"

    @patch("requests.post")
    def test_bearer_auth_handles_token_without_expires(
        self, mock_post, auth_handler, mock_redis
    ):
        """Test Bearer auth handles tokens without expires_in field."""
        mock_redis.get.return_value = None
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "token"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        headers = auth_handler.get_auth_headers()
        assert headers["Authorization"] == "Bearer token"


class TestAuthHandlerEdgeCases:
    """Test edge cases and error handling."""

    def test_basic_auth_returns_headers(self):
        """Test that basic auth returns proper authorization headers."""
        auth_config = AuthConfig(method=AuthMethod.BASIC)
        handler = AuthHandler(
            auth_config=auth_config,
            data_source_id="test-ds-id",
            credentials={"CLIENT_ID": "user", "CLIENT_SECRET": "pass"},
            cache=None,
        )

        headers = handler.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")

    def test_invalid_auth_method(self):
        """Test handling of invalid auth method."""
        # This would normally be caught by Pydantic, but test the handler
        auth_config = Mock()
        auth_config.method = "INVALID_METHOD"

        handler = AuthHandler(
            auth_config=auth_config,
            data_source_id="test-ds-id",
            credentials={"CLIENT_ID": "user", "CLIENT_SECRET": "pass"},
            cache=None,
        )

        headers = handler.get_auth_headers()
        assert headers == {}
