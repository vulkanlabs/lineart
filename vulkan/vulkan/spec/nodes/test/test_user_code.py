import pytest
from vulkan.spec.nodes.user_code import udf

sc = """
if input_node["score"] > 500:
    return "a"
return "b"
"""


@pytest.mark.parametrize(
    "source_code, argnames, expected",
    [
        (
            sc,
            ["input_node"],
            """
def _udf_test(*args, **kwargs):
    if "input_node" not in kwargs:
        raise ValueError("Missing required argument 'input_node'")
    input_node = kwargs.get("input_node")
    
    if input_node["score"] > 500:
        return "a"
    return "b"
""",
        ),
        (
            sc,
            None,
            """
def _udf_test(*args, **kwargs):
    if input_node["score"] > 500:
        return "a"
    return "b"
""",
        ),
    ],
)
def test_udf_argnames(source_code, argnames, expected):
    result = udf("test", source_code, argnames)
    assert result == expected
