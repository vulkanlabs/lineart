from enum import Enum

from vulkan_dagster.core.graph import Graph
from vulkan_dagster.core.nodes import (
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
        dependencies={"input": input_node.name},
    )
    node_b = TransformNode(
        name="b",
        description="Node B",
        func=lambda inputs: inputs,
        dependencies={"input": node_a.name},
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
        dependencies={"input": node_b.name},
    )

    approved = TerminateNode(
        "approved",
        "Approved",
        return_status=DummyStatus.APPROVED,
        dependencies={"input": (branch.name, "approved")},
    )
    denied = TerminateNode(
        "denied",
        "Denied",
        return_status=DummyStatus.DENIED,
        dependencies={"input": (branch.name, "denied")},
    )

    graph = Graph(
        nodes=[input_node, node_a, node_b, branch, approved, denied],
        input_schema={"cpf": str},
    )

    print("Nodes: ", graph.node_definitions)
    print("Edges: ", graph.dependency_definitions)
