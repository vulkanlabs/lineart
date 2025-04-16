from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes import BranchNode, NodeType, TransformNode
from vulkan_public.spec.nodes.metadata import BranchNodeMetadata, TransformNodeMetadata


def test_transform_node():
    def example_function(inputs):
        return inputs

    node = TransformNode(
        name="test",
        description="Test Transform Node",
        func=example_function,
        dependencies={"inputs": Dependency("input_node")},
    )

    assert node.node_dependencies() == [Dependency("input_node")]

    node_definition = node.node_definition()
    print(node.node_definition())

    assert isinstance(node_definition.metadata, TransformNodeMetadata)

    expected_spec = {
        "name": "test",
        "node_type": NodeType.TRANSFORM.value,
        "description": "Test Transform Node",
        "dependencies": {
            "inputs": {
                "node": "input_node",
                "output": None,
                "key": None,
                "hierarchy": None,
            }
        },
        "metadata": {
            "source_code": """def example_function(inputs):
    return inputs
""",
        },
    }
    assert node.to_dict() == expected_spec

    inputs = {"value": 5}
    node_from_spec = TransformNode.from_dict(node.to_dict())
    assert node_from_spec.func(inputs) == node.func(inputs)


def test_branch_node():
    def example_branch(score):
        if score > 500:
            return "A"
        return "B"

    node = BranchNode(
        name="test",
        description="Test Branch Node",
        func=example_branch,
        choices=["A", "B"],
        dependencies={"score": Dependency("model_a")},
    )

    assert node.node_dependencies() == [Dependency("model_a")]

    node_definition = node.node_definition()
    print(node.node_definition())

    assert isinstance(node_definition.metadata, BranchNodeMetadata)

    expected_spec = {
        "name": "test",
        "node_type": NodeType.BRANCH.value,
        "description": "Test Branch Node",
        "dependencies": {
            "score": {
                "node": "model_a",
                "output": None,
                "key": None,
                "hierarchy": None,
            }
        },
        "metadata": {
            "choices": ["A", "B"],
            "source_code": """def example_branch(score):
    if score > 500:
        return "A"
    return "B"
""",
        },
    }
    assert node.to_dict() == expected_spec

    score = 700
    node_from_spec = BranchNode.from_dict(node.to_dict())
    assert node_from_spec.func(score) == node.func(score)
