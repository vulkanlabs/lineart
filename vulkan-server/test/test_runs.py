import os

import pytest
from vulkan_public.cli import client as vulkan
from vulkan_public.cli.context import Context


@pytest.fixture
def context() -> Context:
    return Context()


@pytest.fixture
def current_dir() -> str:
    return os.path.abspath(os.path.dirname(__file__))


def test_create_run_by_policy_id_succeeds(context, current_dir):
    policy_path = "resources/valid/policies/base"
    policy_id = vulkan.policy.create_policy(
        ctx=context,
        name=policy_path,
        description="",
    )
    assert policy_id is not None
    assert len(policy_id) > 0

    policy_version_id = vulkan.policy.create_policy_version(
        ctx=context,
        policy_id=policy_id,
        version_name="v-test-run",
        repository_path=os.path.join(current_dir, policy_path),
    )
    assert policy_version_id is not None
    assert len(policy_version_id) > 0

    vulkan.policy.set_active_version(context, policy_id, policy_version_id)

    run_id, success = vulkan.run.trigger_run_by_policy_id(
        ctx=context,
        policy_id=policy_id,
        input_data={"cpf": "1", "scr_score": 600},
        timeout=20,
        time_step=5,
    )

    assert run_id is not None, "Failed to create run"
    assert success, f"Run execution failed: {run_id}"


def test_create_run_by_policy_id_with_invalid_data(context, current_dir):
    policy_path = "resources/valid/policies/base"
    policy_id = vulkan.policy.create_policy(
        ctx=context,
        name=policy_path,
        description="",
    )
    assert policy_id is not None
    assert len(policy_id) > 0

    policy_version_id = vulkan.policy.create_policy_version(
        ctx=context,
        policy_id=policy_id,
        version_name="v-test-run",
        repository_path=os.path.join(current_dir, policy_path),
    )
    assert policy_version_id is not None
    assert len(policy_version_id) > 0

    vulkan.policy.set_active_version(context, policy_id, policy_version_id)

    # Wrong type: Expects string, received int
    with pytest.raises(ValueError, match="Invalid scalar"):
        vulkan.run.trigger_run_by_policy_id(
            ctx=context, policy_id=policy_id, input_data={"cpf": 1, "scr_score": 600}
        )

    # Missing required field
    with pytest.raises(ValueError, match="Missing required config entry"):
        vulkan.run.trigger_run_by_policy_id(
            ctx=context, policy_id=policy_id, input_data={"cpf": "1"}
        )

    # Extra field
    with pytest.raises(ValueError, match="unexpected config entry"):
        vulkan.run.trigger_run_by_policy_id(
            ctx=context,
            policy_id=policy_id,
            input_data={"cpf": "1", "scr_score": 600, "extra": "field"},
        )


def test_create_run_by_policy_id_with_invalid_id(context):
    # Extra field
    with pytest.raises(ValueError, match="Invalid policy_id: invalid-id"):
        vulkan.run.trigger_run_by_policy_id(
            ctx=context,
            policy_id="invalid-id",
            input_data={"cpf": "1", "scr_score": 600},
        )


def test_create_run_with_exotic_dependency(context):
    policy_path = "resources/valid/policies/with_exotic_dependency/"
    policy_id = vulkan.policy.create_policy(
        ctx=context,
        name=policy_path,
        description="",
    )
    assert policy_id is not None
    assert len(policy_id) > 0

    policy_version_id = vulkan.policy.create_policy_version(
        ctx=context,
        policy_id=policy_id,
        version_name="v-test-run",
        repository_path=policy_path,
    )
    assert policy_version_id is not None
    assert len(policy_version_id) > 0

    vulkan.policy.set_active_version(context, policy_id, policy_version_id)

    run_id, success = vulkan.run.trigger_run_by_policy_id(
        ctx=context,
        policy_id=policy_id,
        input_data={"cpf": "1", "scr_score": 600},
        timeout=20,
        time_step=5,
    )

    assert run_id is not None, "Failed to create run"
    assert success, f"Run execution failed: {run_id}"
