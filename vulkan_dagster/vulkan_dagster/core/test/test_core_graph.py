from enum import Enum

from vulkan_dagster.core.graph import Graph
from vulkan_dagster.core.nodes import (
    BranchNode,
    InputNode,
    TerminateNode,
    TransformNode,
)
from vulkan_dagster.core.component import ComponentGraph


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


def test_core_graph_with_component():
    input_schema = {"cpf": str}
    input_node = InputNode("Input Node", input_schema)

    node_a = TransformNode(
        name="a",
        description="Node A",
        func=lambda inputs: inputs,
        dependencies={"input": input_node.name},
    )
    component_name = "component"
    component_output_name = ComponentGraph.make_output_node_name(component_name)
    node_b = TransformNode(
        name=component_output_name,
        description="Node B",
        func=lambda inputs: inputs,
        dependencies={"input": node_a.name},
    )
    component = ComponentGraph(
        name=component_name,
        description="Component",
        nodes=[node_a, node_b],
        input_schema=input_schema,
        dependencies={"input": input_node.name}
    )

    approved = TerminateNode(
        "approved",
        "Approved",
        return_status=DummyStatus.APPROVED,
        dependencies={"input": component_output_name},
    )

    graph = Graph(
        nodes=[input_node, component, approved],
        input_schema=input_schema,
    )

    print("Nodes: ", graph.node_definitions)
    print("Edges: ", graph.dependency_definitions)
