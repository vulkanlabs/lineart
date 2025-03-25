import pytest

from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.nodes import BranchNode, InputNode, NodeType


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
                "description": "Optional node Description",
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
def test_from_spec_input_node(spec):
    node = InputNode.from_dict(spec)
    assert node.name == spec["name"]
    assert node.type.value == spec["node_type"]
    assert node.description == spec.get("description", None)
    round_trip = node.node_definition().to_dict()
    assert round_trip == spec


@pytest.mark.parametrize(
    ["spec"],
    [
        (
            {
                "name": "branch",
                "node_type": NodeType.BRANCH.value,
                "dependencies": {},  # TODO: This is a bit boring to add in tests
                "metadata": {
                    "choices": ["A", "B"],
                    "source": """
return 10**2
""",
                },
            },
        ),
    ],
)
def test_from_spec_branch_node(spec):
    node = BranchNode.from_dict(spec)
    assert node.name == spec["name"]
    assert node.type.value == spec["node_type"]
    assert node.description == spec.get("description", None)
    round_trip = node.node_definition().to_dict()
    assert round_trip == spec
