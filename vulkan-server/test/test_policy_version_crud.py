import pytest
from vulkan.cli import client as vulkan
from vulkan.cli.context import Context


@pytest.fixture
def context() -> Context:
    return Context()


pytestmark = pytest.mark.integration


def test_policy_version_crud_create(context):
    input_schema = {"cpf": "str"}
    empty_spec = {"nodes": [], "input_schema": input_schema}
    # Create a policy
    policy_id = vulkan.policy.create_policy(
        ctx=context,
        name="test_policy",
        description="",
    )
    assert policy_id is not None
    assert len(policy_id) > 0
    policy_version = vulkan.policy_version.create(
        ctx=context,
        policy_id=policy_id,
        version_name="v1.0",
        input_schema=input_schema,
        requirements=[],
        spec=empty_spec,
    )
    assert policy_version is not None
    assert policy_version["requirements"] == []

    policy_version_id = policy_version["policy_version_id"]
    policy_version_from_read = vulkan.policy_version.get(
        ctx=context,
        policy_version_id=policy_version_id,
    )

    assert policy_version_from_read is not None
    assert policy_version_from_read["policy_version_id"] == policy_version_id
    assert policy_version == policy_version_from_read

    vulkan.policy_version.delete_policy_version(
        ctx=context,
        policy_version_id=policy_version_id,
    )
    vulkan.policy.delete_policy(context, policy_id=policy_id)


def test_policy_version_crud_update(context):
    input_schema = {"cpf": "str"}
    empty_spec = {
        "nodes": [],
        "input_schema": input_schema,
        "config_variables": None,
    }

    # Create a policy
    policy_id = vulkan.policy.create_policy(
        ctx=context,
        name="test_policy",
        description="",
    )
    assert policy_id is not None
    assert len(policy_id) > 0

    policy_version = vulkan.policy_version.create(
        ctx=context,
        policy_id=policy_id,
        version_name="v1.0",
        input_schema=input_schema,
        requirements=[],
        spec=empty_spec,
    )
    assert policy_version is not None
    assert policy_version["requirements"] == []
    assert policy_version["spec"] == empty_spec

    policy_version_updated = vulkan.policy_version.update(
        ctx=context,
        policy_version_id=policy_version["policy_version_id"],
        version_name="v1.1",
        input_schema=input_schema,
        requirements=["numpy"],
        spec=empty_spec,
    )
    assert policy_version_updated is not None
    assert policy_version_updated["requirements"] == ["numpy"]
    assert policy_version_updated["spec"] == empty_spec
    assert (
        policy_version_updated["policy_version_id"]
        == policy_version["policy_version_id"]
    )
    assert policy_version_updated["alias"] == "v1.1"
    assert policy_version_updated["input_schema"] == input_schema

    vulkan.policy_version.delete_policy_version(
        ctx=context,
        policy_version_id=policy_version["policy_version_id"],
    )
    vulkan.policy.delete_policy(context, policy_id=policy_id)
