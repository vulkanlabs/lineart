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

    # Create a policy version
    policy_version_id = vulkan.policy.create_policy_version(
        ctx=context,
        policy_id=policy_id,
        version_name="v1.0",
        input_schema={"cpf": "str"},
        requirements=[],
        spec={},
    )
    assert policy_version_id is not None
    assert len(policy_version_id) > 0
