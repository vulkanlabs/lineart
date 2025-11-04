import pytest
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.graph import sort_nodes
from vulkan.spec.nodes import BranchNode, DataInputNode, TerminateNode, TransformNode
from vulkan.spec.policy import PolicyDefinition


def test_input_node_name_is_reserved():
    invalid_node = TransformNode(
        name=INPUT_NODE,
        description="Node with invalid name",
        func=lambda inputs: inputs,
        dependencies={},
    )

    with pytest.raises(ValueError, match=f"`{INPUT_NODE}` is reserved"):
        _ = PolicyDefinition(
            nodes=[invalid_node],
            input_schema={},
        )


def test_sort_nodes():
    data_source = DataInputNode(
        name="data_source",
        description="Get external data from a provider",
        data_source="data-source:api:v0.0.1",
        dependencies={"data": Dependency(INPUT_NODE)},
    )

    branch = BranchNode(
        func=lambda _: None,
        name="branch",
        description="Make a decision based on the data source",
        dependencies={
            "bureau": Dependency(data_source.name),
        },
        choices=["approved", "denied"],
    )

    approved = TerminateNode(
        name="approved",
        description="Approve customer based on the score",
        return_status="APPROVED",
        dependencies={"condition": Dependency("branch", "approved")},
    )

    denied = TerminateNode(
        name="denied",
        description="Deny customers that are below minimum",
        return_status="DENIED",
        dependencies={"condition": Dependency("branch", "denied")},
    )

    nodes = [data_source, branch, approved, denied]
    policy_def = PolicyDefinition(
        nodes=nodes,
        input_schema={},
    )
    result = sort_nodes(policy_def.nodes, policy_def.edges)

    assert result == nodes
