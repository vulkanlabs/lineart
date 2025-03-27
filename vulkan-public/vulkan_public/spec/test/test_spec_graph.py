import pytest

from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.nodes import TransformNode
from vulkan_public.spec.policy import PolicyDefinition


def test_input_node_name_is_reserved():
    invalid_node = TransformNode(
        name=INPUT_NODE,
        description="Node with invalid name",
        func=lambda inputs: inputs,
        dependencies={},
    )

    with pytest.raises(ValueError, match=f"`{INPUT_NODE}` is reserved"):
        _ = PolicyDefinition(
            nodes=[invalid_node],
            input_schema={},
        )


@pytest.fail("Test not implemented")
def test_sort_nodes():
    pass
