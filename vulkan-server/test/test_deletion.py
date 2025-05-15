# import pytest
# from vulkan.cli.client import policy, policy_version
# from vulkan.cli.context import Context


# def _create_policy(ctx):
#     return policy.create_policy(
#         ctx,
#         name="test_policy",
#     )


# def _create_policy_version(ctx, policy_id):
#     return policy.create_policy_version(
#         ctx,
#         policy_id=policy_id,
#         version_name="v0.0.1",
#         repository_path="resources/valid/policies/base/",
#     )


# def test_resource_deletion():
#     ctx = Context()
#     policy_id = _create_policy(ctx)
#     policy.delete_policy(ctx, policy_id)
#     ctx.logger.info("PASSED: delete policy without versions")

#     policy_id = _create_policy(ctx)

#     policy_version_id = _create_policy_version(ctx, policy_id)
#     policy_version.delete_policy_version(ctx, policy_version_id)
#     ctx.logger.info("PASSED: delete inactive policy version")

#     policy_version_id = _create_policy_version(ctx, policy_id)

#     with pytest.raises(Exception):
#         policy.delete_policy(ctx, policy_id)
#     ctx.logger.info("PASSED: can't delete policy with versions")

#     policy.set_active_version(ctx, policy_id, policy_version_id)

#     with pytest.raises(Exception):
#         policy_version.delete_policy_version(ctx, policy_version_id)
#     ctx.logger.info("PASSED: can't delete active policy version")

#     policy.unset_active_version(ctx, policy_id)

#     policy_version.delete_policy_version(ctx, policy_version_id)
#     policy.delete_policy(ctx, policy_id)
#     ctx.logger.info("PASSED: ordered cleanup")
