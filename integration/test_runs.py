import pytest
from lineart_sdk import Lineart, models
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import BranchNode, TerminateNode
from vulkan.spec.policy import PolicyDefinition


@pytest.fixture
def client() -> Lineart:
    return Lineart(server_url="http://localhost:6001")


pytestmark = pytest.mark.integration


def _create_test_policy_definition():
    """Create a simple test policy definition"""

    def check_score(input_node):
        if input_node["scr_score"] >= 500:
            return "high"
        return "low"

    branch_node = BranchNode(
        name="score_check",
        func=check_score,
        choices=["high", "low"],
        dependencies={INPUT_NODE: Dependency(INPUT_NODE)},
    )

    high_score = TerminateNode(
        name="high_score",
        return_status="APPROVED",
        dependencies={"condition": Dependency("score_check", "high")},
    )

    low_score = TerminateNode(
        name="low_score",
        return_status="REJECTED",
        dependencies={"condition": Dependency("score_check", "low")},
    )

    return PolicyDefinition(
        nodes=[branch_node, high_score, low_score],
        input_schema={"cpf": "str", "scr_score": "int"},
    )


def test_create_run_by_policy_id_succeeds(client: Lineart):
    # Create policy
    policy = client.policies.create(
        name="test_policy",
        description="Test policy for runs",
    )
    policy_id = policy.policy_id

    # Create and update policy version
    version_name = "v-test-run"
    policy_version = client.policy_versions.create(
        policy_id=policy_id, alias=version_name
    )
    policy_version_id = policy_version.policy_version_id

    # Update with the test policy definition
    test_policy_def = _create_test_policy_definition()
    policy_version = client.policy_versions.update(
        policy_version_id=policy_version_id,
        alias=version_name,
        workflow=models.WorkflowBase(
            spec=test_policy_def.to_dict(),
            requirements=[],
        ),
    )

    # Set active version using allocation strategy
    client.policies.update(
        policy_id=policy_id,
        allocation_strategy=models.PolicyAllocationStrategy(
            choice=[{"policy_version_id": policy_version_id, "frequency": 1000}]
        ),
    )

    # Trigger run
    run_group = client.policies.create_run_group(
        policy_id=policy_id,
        input_data={"cpf": "1", "scr_score": 600},
    )

    assert run_group.run_group_id is not None, "Failed to create run"

    # Get run data to verify execution
    run_id = run_group.runs.main
    run_data = client.runs.get_data(run_id=run_id)
    assert run_data is not None, f"Run execution failed: {run_id}"

    # Cleanup
    client.policies.update(policy_id=policy_id, allocation_strategy=None)
    client.policy_versions.delete(policy_version_id=policy_version_id)
    client.policies.delete(policy_id=policy_id)


def test_create_run_by_policy_version_id_succeeds(client: Lineart):
    # Create policy
    policy = client.policies.create(
        name="test_policy_version_run",
        description="Test policy for version-specific runs",
    )
    policy_id = policy.policy_id

    # Create and update policy version
    version_name = "v-test-version-run"
    policy_version = client.policy_versions.create(
        policy_id=policy_id, alias=version_name
    )
    policy_version_id = policy_version.policy_version_id

    # Update with the test policy definition
    test_policy_def = _create_test_policy_definition()
    policy_version = client.policy_versions.update(
        policy_version_id=policy_version_id,
        alias=version_name,
        workflow=models.WorkflowBase(
            spec=test_policy_def.to_dict(),
            requirements=[],
        ),
    )

    # Trigger run by policy version ID
    run = client.policy_versions.create_run(
        policy_version_id=policy_version_id,
        input_data={"cpf": "1", "scr_score": 600},
    )

    assert run.run_id is not None, "Failed to create run"

    # Get run data to verify execution
    run_data = client.runs.get_data(run_id=run.run_id)
    assert run_data is not None, f"Run execution failed: {run.run_id}"

    # Cleanup
    client.policy_versions.delete(policy_version_id=policy_version_id)
    client.policies.delete(policy_id=policy_id)


def test_create_run_with_invalid_data(client: Lineart):
    # Create policy
    policy = client.policies.create(
        name="test_policy_invalid",
        description="Test policy for invalid data",
    )
    policy_id = policy.policy_id

    # Create and update policy version
    version_name = "v-test-invalid"
    policy_version = client.policy_versions.create(
        policy_id=policy_id, alias=version_name
    )
    policy_version_id = policy_version.policy_version_id

    # Update with the test policy definition
    test_policy_def = _create_test_policy_definition()
    policy_version = client.policy_versions.update(
        policy_version_id=policy_version_id,
        alias=version_name,
        workflow=models.WorkflowBase(
            spec=test_policy_def.to_dict(),
            requirements=[],
        ),
    )

    # Set active version
    client.policies.update(
        policy_id=policy_id,
        allocation_strategy=models.PolicyAllocationStrategy(
            choice=[{"policy_version_id": policy_version_id, "frequency": 1000}]
        ),
    )

    # Wrong type: Expects string, received int
    with pytest.raises(Exception):
        client.policies.create_run_group(
            policy_id=policy_id, input_data={"cpf": 1, "scr_score": 600}
        )

    # Missing required field
    with pytest.raises(Exception):
        client.policies.create_run_group(policy_id=policy_id, input_data={"cpf": "1"})

    # Extra field
    with pytest.raises(Exception):
        client.policies.create_run_group(
            policy_id=policy_id,
            input_data={"cpf": "1", "scr_score": 600, "extra": "field"},
        )

    # Cleanup
    client.policies.update(policy_id=policy_id, allocation_strategy=None)
    client.policy_versions.delete(policy_version_id=policy_version_id)
    client.policies.delete(policy_id=policy_id)


def test_create_run_with_invalid_policy_id(client: Lineart):
    # Invalid policy ID
    with pytest.raises(Exception):
        client.policies.create_run_group(
            policy_id="invalid-id",
            input_data={"cpf": "1", "scr_score": 600},
        )
