from enum import Enum

import pytest

from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import BranchNode, InputNode, NodeType, TerminateNode
from vulkan.spec.nodes.transform import TransformNode


class ExampleReturnStatus(Enum):
    SUCCESS = "SUCCESS"


TEST_TABLE = {
    "Input Node - Simple": (
        InputNode,
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
    "Input Node - Complete": (
        InputNode,
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
    "Branch Node - Simple": (
        BranchNode,
        {
            "name": "branch",
            "node_type": NodeType.BRANCH.value,
            "dependencies": {},
            "metadata": {
                "choices": ["A", "B"],
                "source_code": """
return 10**2
            """,
            },
        },
    ),
    "Branch Node - With Import": (
        BranchNode,
        {
            "name": "branch",
            "node_type": NodeType.BRANCH.value,
            "description": "Optional node Description",
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
            "metadata": {
                "choices": ["A", "B"],
                "source_code": """
import os
os.environ
            """,
            },
        },
    ),
    "Transform Node - Simple": (
        TransformNode,
        {
            "name": "transform",
            "node_type": NodeType.TRANSFORM.value,
            "dependencies": {},
            "metadata": {
                "source_code": """
return 10**2
            """,
            },
        },
    ),
    "Transform Node - With Import": (
        TransformNode,
        {
            "name": "transform",
            "node_type": NodeType.TRANSFORM.value,
            "description": "Optional node Description",
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
            "metadata": {
                "source_code": """
import os
os.environ
            """,
            },
        },
    ),
    "Terminate Node - Simple": (
        TerminateNode,
        {
            "name": "terminate_a",
            "node_type": NodeType.TERMINATE.value,
            "metadata": {
                "return_status": "SUCCESS",
            },
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
        },
    ),
    "Terminate Node - With Enum": (
        TerminateNode,
        {
            "name": "terminate_b",
            "node_type": NodeType.TERMINATE.value,
            "description": "Optional node Description",
            "metadata": {
                "return_status": ExampleReturnStatus.SUCCESS,
            },
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
        },
    ),
    # TODO: Data input tests
}


@pytest.mark.parametrize(
    ["node_cls", "spec"],
    [(cls, spec) for cls, spec in TEST_TABLE.values()],
    ids=list(TEST_TABLE.keys()),
)
def test_node_from_spec(node_cls, spec):
    node = node_cls.from_dict(spec)
    assert node.name == spec["name"]
    assert node.type.value == spec["node_type"]
    assert node.description == spec.get("description", None)
