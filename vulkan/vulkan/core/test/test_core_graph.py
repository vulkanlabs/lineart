from enum import Enum

import pytest

from vulkan.core.component import (
    ComponentDefinition,
    ComponentGraph,
    ComponentInstance,
    InstanceParam,
    check_all_parameters_specified,
)
from vulkan.core.dependency import Dependency
from vulkan.core.graph import Graph
from vulkan.core.nodes import (
    BranchNode,
    HTTPConnectionNode,
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
        dependencies={"input": Dependency(input_node.name)},
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


def test_core_graph_with_component_definition():
    configurable_node = HTTPConnectionNode(
        name="query",
        description="Get SCR score",
        method="GET",
        headers={},
        params={},
        dependencies={"body": Dependency("body")},
        url=InstanceParam("server_url"),
    )

    definition = ComponentDefinition(
        nodes=[configurable_node],
        input_schema={"cpf": str},
        instance_params_schema={"server_url": str},
    )

    correct_instance = ComponentInstance(
        name="test_cmp",
        version="vtest",
        config={
            "name": "scr_query_component",
            "description": "Get SCR score",
            "dependencies": {"body": Dependency("input_node")},
            "instance_params": {"server_url": "test_url"},
        },
    )

    check_all_parameters_specified(definition, correct_instance)
    component = ComponentGraph.from_spec(definition, correct_instance)
    assert component.nodes[-1].url == "test_url"

    missing_params = ComponentInstance(
        name="test_cmp",
        version="vtest",
        config={
            "name": "scr_query_component",
            "description": "Get SCR score",
            "dependencies": {"body": Dependency("input_node")},
        },
    )

    with pytest.raises(ValueError):
        check_all_parameters_specified(definition, missing_params)

    missing_value = ComponentInstance(
        name="test_cmp",
        version="vtest",
        config={
            "name": "scr_query_component",
            "description": "Get SCR score",
            "dependencies": {"body": Dependency("input_node")},
            "instance_params": {},
        },
    )

    with pytest.raises(ValueError):
        check_all_parameters_specified(definition, missing_value)

    incorrect_type = ComponentInstance(
        name="test_cmp",
        version="vtest",
        config={
            "name": "scr_query_component",
            "description": "Get SCR score",
            "dependencies": {"body": Dependency("input_node")},
            "instance_params": {"server_url": 1},
        },
    )

    with pytest.raises(TypeError):
        check_all_parameters_specified(definition, incorrect_type)
