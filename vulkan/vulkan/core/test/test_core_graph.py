from enum import Enum

from vulkan.core.component import ComponentGraph
from vulkan.core.dependency import Dependency
from vulkan.core.graph import Graph
from vulkan.core.nodes import (
    BranchNode,
    InputNode,
    TerminateNode,
    TransformNode,
)


class DummyStatus(Enum):
    APPROVED = "approved"
    DENIED = "denied"


def test_core_graph_trivial():
    input_node = InputNode("Input Node", {"cpf": str})
    node_a = TransformNode(
        name="a",
        description="Node A",
        func=lambda inputs: inputs,
        dependencies={"input": Dependency(input_node.name)},
    )
    node_b = TransformNode(
        name="b",
        description="Node B",
        func=lambda inputs: inputs,
        dependencies={"input": Dependency(node_a.name)},
    )

    def branch_fn(inputs: dict):
        if inputs["cpf"] == "1":
            return DummyStatus.APPROVED.value
        return DummyStatus.DENIED.value

    branch = BranchNode(
        "branch",
        "Branch Node",
        func=branch_fn,
        outputs=["approved", "denied"],
        dependencies={"input": Dependency(node_b.name)},
    )

    approved = TerminateNode(
        "approved",
        "Approved",
        return_status=DummyStatus.APPROVED,
        dependencies={"input": Dependency(branch.name, "approved")},
    )
    denied = TerminateNode(
        "denied",
        "Denied",
        return_status=DummyStatus.DENIED,
        dependencies={"input": Dependency(branch.name, "denied")},
    )

    graph = Graph(
        nodes=[input_node, node_a, node_b, branch, approved, denied],
        input_schema={"cpf": str},
    )

    print("Nodes: ", graph.node_definitions)
    print("Edges: ", graph.dependency_definitions)


def test_core_graph_with_component():
    input_schema = {"cpf": str}
    input_node = InputNode("Input Node", input_schema)

    node_a = TransformNode(
        name="a",
        description="Node A",
        func=lambda inputs: inputs,
        dependencies={"input": Dependency("input_node")},
    )
    node_b = TransformNode(
        name="b",
        description="Node B",
        func=lambda inputs: inputs,
        dependencies={"input": Dependency(node_a.name)},
    )
    component = ComponentGraph(
        name="component",
        description="Component",
        nodes=[node_a, node_b],
        input_schema=input_schema,
        dependencies={"input": Dependency(input_node.name)}
    )

    approved = TerminateNode(
        "approved",
        "Approved",
        return_status=DummyStatus.APPROVED,
        dependencies={"input": Dependency("component")},
    )

    graph = Graph(
        nodes=[input_node, component, approved],
        input_schema=input_schema,
    )

    print("Nodes: ", graph.node_definitions)
    print("Edges: ", graph.dependency_definitions)
