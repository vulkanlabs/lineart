import pytest

from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.nodes import InputNode, NodeType


@pytest.mark.parametrize(
    ["spec"],
    [
        (
            {
                "name": INPUT_NODE,
                "node_type": NodeType.INPUT.value,
                "metadata": {
                    "schema": {
                        "cpf": "str",
                    },
                },
            },
        ),
        (
            {
                "name": INPUT_NODE,
                "node_type": NodeType.INPUT.value,
                "metadata": {
                    "schema": {
                        "cpf": "str",
                        "score": "int",
                        "valid": "bool",
                        "test": "float",
                    },
                },
            },
        ),
    ],
)
def test_from_definition_input_node_(spec):
    node = InputNode.from_dict(spec)
    assert node.node_dependencies() == []
    round_trip = node.node_definition().to_dict()
    assert round_trip == spec
