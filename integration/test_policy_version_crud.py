import pytest
from lineart_sdk import Lineart, models


@pytest.fixture
def client() -> Lineart:
    return Lineart(server_url="http://localhost:6001")


pytestmark = pytest.mark.integration


def test_policy_version_crud_create(client: Lineart):
    input_schema = {"cpf": "str"}
    empty_spec = {"nodes": [], "input_schema": input_schema}

    # Create a policy
    policy = client.policies.create(
        name="test_policy",
        description="",
    )
    policy_id = policy.policy_id
    assert policy_id is not None

    version_name = "v1.0"
    policy_version = client.policy_versions.create(
        policy_id=policy_id, alias=version_name
    )
    policy_version_id = policy_version.policy_version_id
    policy_version = client.policy_versions.update(
        policy_version_id=policy_version_id,
        alias=version_name,
        workflow=models.WorkflowBase(
            spec=empty_spec,
            requirements=[],
        ),
    )
    assert policy_version is not None
    assert policy_version.workflow.requirements == []

    policy_version_from_read = client.policy_versions.get(
        policy_version_id=policy_version_id
    )

    assert policy_version_from_read is not None
    assert policy_version_from_read.policy_version_id == policy_version_id
    assert policy_version == policy_version_from_read

    client.policy_versions.delete(policy_version_id=policy_version_id)
    client.policies.delete(policy_id=policy_id)


def test_policy_version_crud_update(client: Lineart):
    input_schema = {"cpf": "str"}
    empty_spec = {"nodes": [], "input_schema": input_schema}

    # Create a policy
    policy = client.policies.create(
        name="test_policy",
        description="",
    )
    policy_id = policy.policy_id
    assert policy_id is not None

    version_name = "v1.0"
    policy_version = client.policy_versions.create(
        policy_id=policy_id, alias=version_name
    )
    policy_version_id = policy_version.policy_version_id
    policy_version = client.policy_versions.update(
        policy_version_id=policy_version_id,
        alias=version_name,
        workflow=models.WorkflowBase(
            spec=empty_spec,
            requirements=[],
        ),
    )
    assert policy_version is not None
    assert policy_version.workflow.requirements == []

    # Update with new requirements
    policy_version_updated = client.policy_versions.update(
        policy_version_id=policy_version_id,
        alias="v1.1",
        workflow=models.WorkflowBase(
            spec=empty_spec,
            requirements=["numpy"],
        ),
    )
    assert policy_version_updated is not None
    assert policy_version_updated.workflow.requirements == ["numpy"]
    assert policy_version_updated.policy_version_id == policy_version_id
    assert policy_version_updated.alias == "v1.1"

    client.policy_versions.delete(policy_version_id=policy_version_id)
    client.policies.delete(policy_id=policy_id)
