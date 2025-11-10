import json
from unittest.mock import Mock, patch

from vulkan.data_source import HTTPSource
from vulkan.http_client import HTTPClient
from vulkan.node_config import RunTimeParam


class TestHTTPClientRaw:
    def test_http_client_raw_with_escape_sequence(self):
        """Test HTTPClient.execute_raw with template escape sequences."""
        config = HTTPSource(
            url="http://url",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "AccessToken": RunTimeParam(param="access_token", value_type="str"),
                "TestHeader": RunTimeParam(param="auto_value"),
            },
            body={
                "q": 'doc{{ "{" }}{{tax_id}}{{"}"}}',
            },
        )
        local_vars = {
            "tax_id": "1234567890",
            "access_token": "mock_access_token",
            "auto_value": "test_auto_value",
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value.__enter__.return_value = mock_client_instance
            mock_client_instance.request.return_value = mock_response

            client = HTTPClient(config)
            response = client.execute_raw(local_variables=local_vars, env_variables={})

            assert response.status_code == 200

            call_args = mock_client_instance.request.call_args
            assert call_args.kwargs["method"] == "POST"
            assert call_args.kwargs["url"] == "http://url"
            assert call_args.kwargs["headers"]["Content-Type"] == "application/json"
            assert call_args.kwargs["headers"]["AccessToken"] == "mock_access_token"
            assert call_args.kwargs["headers"]["TestHeader"] == "test_auto_value"

            # Verify body has correct template substitution
            body = call_args.kwargs["json"]
            assert body["q"] == "doc{1234567890}"


class TestHTTPClient:
    def test_http_client_with_template_substitution(self):
        """Test HTTPClient with template variable substitution."""
        config = HTTPSource(
            url="http://example.com/api/{{endpoint}}",
            method="POST",
            headers={
                "Authorization": "Bearer {{env.token}}",
            },
            body={
                "user_id": "{{user_id}}",
            },
            response_type="JSON",
        )

        client = HTTPClient(config)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user": "john", "id": 123}

        with patch("httpx.Client") as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value.__enter__.return_value = mock_client_instance
            mock_client_instance.request.return_value = mock_response

            result = client.execute(
                local_variables={"endpoint": "users", "user_id": "12345"},
                env_variables={"token": "secret_token"},
            )

            # Verify result
            assert result == {"user": "john", "id": 123}

            # Verify request parameters
            call_args = mock_client_instance.request.call_args
            assert call_args.kwargs["url"] == "http://example.com/api/users"
            assert call_args.kwargs["headers"]["Authorization"] == "Bearer secret_token"
            assert call_args.kwargs["json"]["user_id"] == 12345  # Auto type conversion
