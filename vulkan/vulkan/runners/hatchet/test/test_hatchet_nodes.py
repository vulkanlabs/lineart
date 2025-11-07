from unittest.mock import MagicMock

from hatchet_sdk import Hatchet
from vulkan.core.policy import Policy
from vulkan.runners.hatchet.nodes import (
    HatchetDataInput,
    HatchetTerminate,
    HatchetTransform,
    to_hatchet_nodes,
)
from vulkan.runners.hatchet.policy import HatchetFlow
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import BranchNode, DataInputNode, TerminateNode, TransformNode
from vulkan.spec.policy import PolicyDefinition


def test_data_input_node_conversion():
    """Test DataInputNode to HatchetDataInput conversion."""
    node = DataInputNode(
        name="test_data_input",
        data_source="test_source",
        description="Test data input",
        parameters={"param1": "value1"},
    )

    hatchet_node = HatchetDataInput.from_spec(node)

    assert hatchet_node.name == "test_data_input"
    assert hatchet_node.data_source == "test_source"
    assert hatchet_node.description == "Test data input"
    assert hatchet_node.parameters == {"param1": "value1"}
    assert hatchet_node.task_name == "test_data_input"
    assert callable(hatchet_node.task_fn())


def test_transform_node_conversion():
    """Test TransformNode to HatchetTransform conversion."""

    def test_func(x):
        return x * 2

    node = TransformNode(
        name="test_transform",
        description="Test transform",
        func=test_func,
        dependencies={"input": Dependency(INPUT_NODE)},
    )

    hatchet_node = HatchetTransform.from_spec(node)

    assert hatchet_node.name == "test_transform"
    assert hatchet_node.description == "Test transform"
    assert hatchet_node.func == test_func
    assert hatchet_node.task_name == "test_transform"
    assert callable(hatchet_node.task_fn())


def test_terminate_node_conversion():
    """Test TerminateNode to HatchetTerminate conversion."""
    node = TerminateNode(
        name="test_terminate",
        description="Test terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency(INPUT_NODE)},
    )

    hatchet_node = HatchetTerminate.from_spec(node)

    assert hatchet_node.name == "test_terminate"
    assert hatchet_node.description == "Test terminate"
    assert hatchet_node.return_status == "SUCCESS"
    assert hatchet_node.task_name == "test_terminate"
    assert callable(hatchet_node.task_fn())


def test_to_hatchet_nodes():
    """Test conversion of multiple nodes."""
    nodes = [
        DataInputNode(name="data_input", data_source="test", dependencies={}),
        TransformNode(
            name="transform", description="test", func=lambda x: x, dependencies={}
        ),
        TerminateNode(
            name="terminate",
            description="test",
            return_status="SUCCESS",
            dependencies={},
        ),
    ]

    hatchet_nodes = to_hatchet_nodes(nodes)

    assert len(hatchet_nodes) == 3
    assert isinstance(hatchet_nodes[0], HatchetDataInput)
    assert isinstance(hatchet_nodes[1], HatchetTransform)
    assert isinstance(hatchet_nodes[2], HatchetTerminate)


def test_regression_hatchet_flow_with_unsorted_node_list():
    def is_even_fn(input_node):
        if input_node["number"] % 2 == 0:
            return "even"
        return "odd"

    branch_node_1 = BranchNode(
        name="branch_node_1",
        func=is_even_fn,
        choices=["even", "odd"],
        dependencies={INPUT_NODE: Dependency(INPUT_NODE)},
    )

    is_even = TerminateNode(
        name="is_even",
        return_status="Great",
        dependencies={"condition": Dependency("branch_node_1", "even")},
    )

    is_odd = TerminateNode(
        name="is_odd",
        return_status="Too_Bad",
        dependencies={"condition": Dependency("branch_node_1", "odd")},
    )

    policy_def = PolicyDefinition(
        nodes=[
            is_even,
            is_odd,
            branch_node_1,
        ],
        input_schema={"number": "int"},
    )
    policy = Policy.from_definition(policy_def)

    flow = HatchetFlow(
        nodes=policy.nodes,
        hatchet=Hatchet(client=MagicMock(), config=MagicMock()),
    )
    flow.create_workflow()
