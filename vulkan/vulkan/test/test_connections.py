import json

from vulkan.connections import make_request
from vulkan.data_source import HTTPSource
from vulkan.node_config import RunTimeParam


class TestMakeRequest:
    def test_make_request_with_escape_sequence(self):
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
        req = make_request(config, local_variables=local_vars, env_variables={})

        assert req.headers.get("Content-Type") == "application/json"
        assert req.headers.get("AccessToken") == "mock_access_token"
        assert req.headers.get("TestHeader") == "test_auto_value"
        raw_body = req.body.decode("utf-8")
        body = json.loads(raw_body)
        assert body.get("q") == "doc{1234567890}"
