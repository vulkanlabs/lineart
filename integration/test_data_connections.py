"""Tests for data connections, data sources, and policies with DataInputNode and ConnectionNode."""

import uuid

import pytest
from lineart_sdk import Lineart
from lineart_sdk.models import (
    CachingOptions,
    DataSource,
    EnvVarConfig,
    HTTPSource,
    Policy,
    ResponseType,
    RetryPolicy,
    RunTimeParam,
    WorkflowBase,
)
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import (
    ConnectionNode,
    DataInputNode,
    DecisionNode,
    Node,
    TerminateNode,
    TransformNode,
)
from vulkan.spec.nodes.metadata import DecisionCondition, DecisionType
from vulkan.spec.policy import PolicyDefinition

BASE_URL = "http://localhost:6001"

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    """Create a Lineart client for tests."""
    with Lineart(server_url=BASE_URL) as client:
        yield client


@pytest.fixture
def policy(client: Lineart):
    """Create a test policy."""
    policy = client.policies.create(
        name="TestDataConnectionsPolicy",
        description="Test policy for data connections",
    )
    yield policy
    # Cleanup
    try:
        client.policies.delete(policy.policy_id)
    except Exception:
        pass


@pytest.fixture
def data_source(client: Lineart):
    """Create a test data source."""
    unique_suffix = str(uuid.uuid4())[:8]
    api = "test-api"
    version = "1.0"
    ref = f"{api}-v{version}-{unique_suffix}"

    source = HTTPSource(
        url="http://testdata:5000/",
        method="GET",
        headers={"Content-Type": "application/json"},
        params={"full": EnvVarConfig(env="FULL")},
        body={"tax_id": RunTimeParam(param="tax_id")},
        retry=RetryPolicy(
            max_retries=3,
            backoff_factor=1,
        ),
        timeout=5,
        response_type=ResponseType.JSON.value,
    )

    caching = CachingOptions(enabled=True, ttl=3600)

    data_source = client.data_sources.create(
        name=ref,
        description="Test data source",
        source=source,
        caching=caching,
        metadata={"api": api, "version": version},
    )
    yield data_source
    # Cleanup
    try:
        client.data_sources.delete(data_source_id=data_source.data_source_id)
    except Exception:
        pass


def _format_name(name: str) -> str:
    """Format data source name into a valid node name."""
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)


def _create_decision_nodes(api_node: Node):
    """Create the decision logic nodes that are shared across tests.

    Parameters
    ----------
    api_node : Node
        The API node (DataInputNode or ConnectionNode) that provides scores.
    """

    def calculate_decision(context, scores, **kwargs):
        if scores["scr"] > 600:
            return "approved"
        if scores["serasa"] > 800:
            return "analysis"
        return "denied"

    transform_node = TransformNode(
        name="calculate_decision",
        func=calculate_decision,
        dependencies={"scores": Dependency(api_node.name)},
    )

    decision_node = DecisionNode(
        name="decision",
        conditions=[
            DecisionCondition(
                decision_type=DecisionType.IF,
                condition="{{choice == 'approved'}}",
                output="approved",
            ),
            DecisionCondition(
                decision_type=DecisionType.ELSE_IF,
                condition="{{choice == 'analysis'}}",
                output="analysis",
            ),
            DecisionCondition(
                decision_type=DecisionType.ELSE,
                condition=None,
                output="denied",
            ),
        ],
        dependencies={"choice": Dependency(transform_node.name)},
    )

    output_data = {"scores": f"{{{{{api_node.name}}}}}"}

    approved_node = TerminateNode(
        name="approved",
        return_status="approved",
        output_data=output_data,
        dependencies={"condition": Dependency("decision", "approved")},
    )

    analysis_node = TerminateNode(
        name="analysis",
        return_status="analysis",
        output_data=output_data,
        dependencies={"condition": Dependency("decision", "analysis")},
    )

    denied_node = TerminateNode(
        name="denied",
        return_status="denied",
        output_data=output_data,
        dependencies={"condition": Dependency("decision", "denied")},
    )

    return (
        transform_node,
        decision_node,
        approved_node,
        analysis_node,
        denied_node,
    )


def test_data_source_crd(client: Lineart):
    """Test Create, Read, Delete operations for data sources (Update not supported)."""
    # Create
    unique_suffix = str(uuid.uuid4())[:8]
    ref = f"ds-crud-test-{unique_suffix}"

    source = HTTPSource(
        url="http://example.com/api",
        method="POST",
        headers={"Authorization": "Bearer token"},
        body={"key": RunTimeParam(param="input_key")},
        timeout=10,
        response_type=ResponseType.JSON.value,
    )

    data_source = client.data_sources.create(
        name=ref,
        description="CRUD test data source",
        source=source,
        metadata={"test": True},
    )

    assert data_source.name == ref
    assert data_source.description == "CRUD test data source"
    assert data_source.metadata == {"test": True}

    # Read
    fetched = client.data_sources.get(data_source_id=data_source.data_source_id)
    assert fetched.name == data_source.name
    assert fetched.description == data_source.description

    # Note: Data sources cannot be updated after creation
    # Users must delete and recreate if changes are needed

    # List
    all_sources = client.data_sources.list()
    assert any(ds.data_source_id == data_source.data_source_id for ds in all_sources)

    # Delete
    client.data_sources.delete(data_source_id=data_source.data_source_id)

    # # Verify deletion
    ds = client.data_sources.get(data_source_id=data_source.data_source_id)
    assert ds.archived is True


def test_policy_with_data_input_node(
    client: Lineart, policy: Policy, data_source: DataSource
):
    """Test running a policy version with a DataInputNode."""
    # Format the data source name into a valid node name
    node_name = _format_name(data_source.name)

    # Create API node
    api_node = DataInputNode(
        name=node_name,
        data_source=data_source.name,
        parameters={"tax_id": "'{{inputs.tax_id}}'"},
        dependencies={"inputs": Dependency(INPUT_NODE)},
    )

    # Create decision nodes using helper
    transform_node, decision_node, approved_node, analysis_node, denied_node = (
        _create_decision_nodes(api_node)
    )

    # Create policy definition
    policy_def = PolicyDefinition(
        nodes=[
            api_node,
            transform_node,
            decision_node,
            approved_node,
            analysis_node,
            denied_node,
        ],
        input_schema={"tax_id": "str"},
    )

    # Create policy version
    version = client.policy_versions.create(
        policy_id=policy.policy_id,
        alias="v1-data-input",
    )

    # Update with workflow
    updated_version = client.policy_versions.update(
        policy_version_id=version.policy_version_id,
        alias="v1-data-input",
        workflow=WorkflowBase(
            spec=policy_def.to_dict(),
            requirements=[],
        ),
    )

    assert updated_version.alias == "v1-data-input"
    assert updated_version.workflow is not None

    # Run the policy
    run = client.policy_versions.create_run(
        policy_version_id=version.policy_version_id,
        input_data={"tax_id": "123456"},
    )

    assert run.policy_version_id == version.policy_version_id
    assert run.run_id is not None

    # Cleanup
    try:
        client.policy_versions.delete(version.policy_version_id)
    except Exception:
        pass


def test_policy_with_connection_node(client: Lineart, policy: Policy):
    """Test running a policy version with a ConnectionNode."""
    # Create API node
    api_node = ConnectionNode(
        name="test_api_connection",
        url="http://testdata:5000",
        method="GET",
        headers={"Content-Type": "application/json"},
        params={"full": True},
        body={"tax_id": "'{{inputs.tax_id}}'"},
        response_type=ResponseType.JSON.value,
        dependencies={"inputs": Dependency(INPUT_NODE)},
    )

    # Create decision nodes using helper
    transform_node, decision_node, approved_node, analysis_node, denied_node = (
        _create_decision_nodes(api_node)
    )

    # Create policy definition
    policy_def = PolicyDefinition(
        nodes=[
            api_node,
            transform_node,
            decision_node,
            approved_node,
            analysis_node,
            denied_node,
        ],
        input_schema={"tax_id": "str"},
    )

    # Create policy version
    version = client.policy_versions.create(
        policy_id=policy.policy_id,
        alias="v2-connection",
    )

    # Update with workflow
    updated_version = client.policy_versions.update(
        policy_version_id=version.policy_version_id,
        alias="v2-connection",
        workflow=WorkflowBase(
            spec=policy_def.to_dict(),
            requirements=[],
        ),
    )

    assert updated_version.alias == "v2-connection"
    assert updated_version.workflow is not None

    # Run the policy
    run = client.policy_versions.create_run(
        policy_version_id=version.policy_version_id,
        input_data={"tax_id": "789012"},
    )

    assert run.policy_version_id == version.policy_version_id
    assert run.run_id is not None

    # Cleanup
    try:
        client.policy_versions.delete(version.policy_version_id)
    except Exception:
        pass
