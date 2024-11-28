import pytest
from vulkan_public.cli.client import component, policy, policy_version
from vulkan_public.cli.context import Context


def _create_component_version(ctx, component_id):
    return component.create_component_version(
        ctx,
        component_id=component_id,
        version_name="v0.0.1",
        repository_path="resources/valid/components/base/",
    )


def _create_policy(ctx):
    return policy.create_policy(
        ctx,
        name="test_policy",
    )


def _create_policy_version(ctx, policy_id):
    return policy.create_policy_version(
        ctx,
        policy_id=policy_id,
        version_name="v0.0.1",
        repository_path="resources/valid/policies/with_component/",
    )


def test_resource_deletion():
    ctx = Context()
    component_id = component.create_component(ctx, name="test_component")

    component.delete_component(ctx, component_id)
    ctx.logger.info("PASSED: delete component without versions")

    component_id = component.create_component(ctx, name="test_component")
    ctx.logger.info("PASSED: recreate component with the same name")

    component_version_id = _create_component_version(ctx, component_id)

    component.delete_component_version(ctx, component_version_id)
    ctx.logger.info("PASSED: delete dangling component version")

    component_version_id = _create_component_version(ctx, component_id)
    ctx.logger.info("PASSED: recreate component version with the same tag")

    with pytest.raises(Exception):
        component.delete_component(ctx, component_id)
    ctx.logger.info("PASSED: can't delete component with versions")

    policy_id = _create_policy(ctx)
    policy.delete_policy(ctx, policy_id)
    ctx.logger.info("PASSED: delete policy without versions")

    policy_id = _create_policy(ctx)

    policy_version_id = _create_policy_version(ctx, policy_id)
    policy_version.delete_policy_version(ctx, policy_version_id)
    ctx.logger.info("PASSED: delete inactive policy version")

    policy_version_id = _create_policy_version(ctx, policy_id)

    with pytest.raises(Exception):
        policy.delete_policy(ctx, policy_id)
    ctx.logger.info("PASSED: can't delete policy with versions")

    with pytest.raises(Exception):
        component.delete_component_version(ctx, component_version_id)
    ctx.logger.info("PASSED: can't delete component version used by policy")

    policy.set_active_version(ctx, policy_id, policy_version_id)

    with pytest.raises(Exception):
        policy_version.delete_policy_version(ctx, policy_version_id)
    ctx.logger.info("PASSED: can't delete active policy version")

    policy.unset_active_version(ctx, policy_id)

    policy_version.delete_policy_version(ctx, policy_version_id)
    policy.delete_policy(ctx, policy_id)
    component.delete_component_version(ctx, component_version_id)
    component.delete_component(ctx, component_id)
    ctx.logger.info("PASSED: ordered cleanup")
