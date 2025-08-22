import pytest
from lineart_sdk import Lineart, models


@pytest.fixture
def client() -> Lineart:
    return Lineart(server_url="http://localhost:6001")


pytestmark = pytest.mark.integration


def _create_policy(client: Lineart):
    policy = client.policies.create(
        name="test_policy",
        description="",
    )
    return policy.policy_id


def _create_policy_version(client: Lineart, policy_id: str):
    input_schema = {"cpf": "str"}
    empty_spec = {"nodes": [], "input_schema": input_schema}

    policy_version = client.policy_versions.create(policy_id=policy_id, alias="v0.0.1")
    policy_version_id = policy_version.policy_version_id
    policy_version = client.policy_versions.update(
        policy_version_id=policy_version_id,
        alias="v0.0.1",
        workflow=models.WorkflowBase(
            spec=empty_spec,
            requirements=[],
        ),
    )
    return policy_version_id


def test_resource_deletion(client: Lineart):
    policy_id = _create_policy(client)
    client.policies.delete(policy_id=policy_id)
    print("PASSED: delete policy without versions")

    policy_id = _create_policy(client)

    policy_version_id = _create_policy_version(client, policy_id)
    client.policy_versions.delete(policy_version_id=policy_version_id)
    print("PASSED: delete inactive policy version")

    policy_version_id = _create_policy_version(client, policy_id)

    with pytest.raises(Exception):
        client.policies.delete(policy_id=policy_id)
    print("PASSED: can't delete policy with versions")

    client.policies.update(
        policy_id=policy_id,
        allocation_strategy=models.PolicyAllocationStrategy(
            choice=[{"policy_version_id": policy_version_id, "frequency": 1000}]
        ),
    )

    with pytest.raises(Exception):
        client.policy_versions.delete(policy_version_id=policy_version_id)
    print("PASSED: can't delete active policy version")

    client.policies.update(policy_id=policy_id, allocation_strategy=None)
    client.policy_versions.delete(policy_version_id=policy_version_id)
    client.policies.delete(policy_id=policy_id)
    print("PASSED: ordered cleanup")
