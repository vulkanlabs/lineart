from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes import TransformNode


def test_transform_node():
    node = TransformNode(
        name="test",
        description="Test Transform Node",
        func=lambda inputs: inputs,
        dependencies={"input": Dependency("input_node")},
    )

    assert node.node_dependencies() == [Dependency("input_node")]
    assert node.node_definition() is not None
    print(node.node_definition())
