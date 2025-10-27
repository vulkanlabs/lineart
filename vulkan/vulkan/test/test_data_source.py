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
