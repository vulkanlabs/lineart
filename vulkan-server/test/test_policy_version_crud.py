import pytest
from vulkan_public.cli import client as vulkan
from vulkan_public.cli.context import Context


@pytest.fixture
def context() -> Context:
    return Context()


pytestmark = pytest.mark.integration


def test_policy_version_crud_create(context):
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
        input_schema={"cpf": "str"},
        requirements=[],
        spec={},
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


def test_policy_version_crud_update(context):
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
        input_schema={"cpf": "str"},
        requirements=[],
        spec={},
    )
    assert policy_version is not None
    assert policy_version["requirements"] == []
    assert policy_version["spec"] == {}

    policy_version_updated = vulkan.policy_version.update(
        ctx=context,
        policy_version_id=policy_version["policy_version_id"],
        version_name="v1.1",
        input_schema={"cpf": "int"},
        requirements=["numpy"],
        spec={},
    )
    assert policy_version_updated is not None
    assert policy_version_updated["requirements"] == ["numpy"]
    assert policy_version_updated["spec"] == {}
    assert (
        policy_version_updated["policy_version_id"]
        == policy_version["policy_version_id"]
    )
    assert policy_version_updated["alias"] == "v1.1"
    assert policy_version_updated["input_schema"] == {"cpf": "int"}
