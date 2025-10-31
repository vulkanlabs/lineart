from vulkan.data_source import HTTPSource
from vulkan.node_config import RunTimeParam


class TestHTTPSource:
    def test_extract_runtime_params(self):
        config = HTTPSource(
            url="https://{{url}}",
            headers={
                "Authorization": {"param": "auth_token"},
                "TestHeader": {"param": "test_header", "value_type": "auto"},
                "accept": RunTimeParam(param="accept_type"),
                "Content-Type": RunTimeParam(param="content_type", value_type="str"),
            },
        )

        params = config.extract_runtime_params()

        assert set(params) == {
            "url",
            "auth_token",
            "test_header",
            "accept_type",
            "content_type",
        }

    def test_extract_runtime_params_with_escape_sequence(self):
        config = HTTPSource(
            url="http://url",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "AccessToken": RunTimeParam(param="access_token", value_type="str"),
                "TokenId": RunTimeParam(param="token_id", value_type="str"),
            },
            body={
                "Datasets": "basic_data",
                "q": 'doc{{ "{" }}{{tax_id}}{{"}"}}',
                "Limit": 1,
            },
        )
        params = config.extract_runtime_params()
        assert set(params) == {"access_token", "token_id", "tax_id"}
