# import os

# import pytest
# from vulkan_public.cli import client as vulkan
# from vulkan_public.cli.context import Context
# from vulkan_public.exceptions import (
#     ConflictingDefinitionsError,
#     DefinitionNotFoundException,
#     InvalidDefinitionError,
# )

# SUCCESS_CASES = [
#     ("resources/valid/policies/base"),
#     ("resources/valid/policies/dangling_node"),
# ]

# FAILURE_CASES = [
#     ("resources/invalid/policies/missing_py_dep", ValueError),
#     ("resources/invalid/policies/no_pyproject", FileNotFoundError),
#     ("resources/invalid/policies/missing_component", ValueError),
#     ("resources/invalid/policies/no_vulkan_config", FileNotFoundError),
#     ("resources/invalid/policies/node_with_reserved_name", ValueError),
# ]

# CLI_FAILURE_CASES = [
#     ("resources/invalid/policies/missing_required_node", InvalidDefinitionError),
#     ("resources/invalid/policies/multiple_definitions", ConflictingDefinitionsError),
#     ("resources/invalid/policies/no_definition", DefinitionNotFoundException),
# ]


# @pytest.fixture
# def context() -> Context:
#     return Context()


# @pytest.fixture
# def current_dir() -> str:
#     return os.path.abspath(os.path.dirname(__file__))


# @pytest.mark.parametrize(
#     "test_case, err_type",
#     FAILURE_CASES,
#     ids=[x[0] for x in FAILURE_CASES],
# )
# def test_create_policy_version_fails(context, current_dir, test_case, err_type):
#     policy_id = vulkan.policy.create_policy(
#         ctx=context,
#         name=test_case,
#         description="",
#     )
#     with pytest.raises(err_type):
#         _ = vulkan.policy.create_policy_version(
#             ctx=context,
#             policy_id=policy_id,
#             version_name="1",
#             repository_path=os.path.join(current_dir, test_case),
#         )


# @pytest.mark.xfail(reason="We need to change the module loading logic for the CLI.")
# @pytest.mark.parametrize(
#     "test_case, err_type",
#     CLI_FAILURE_CASES,
#     ids=[x[0] for x in CLI_FAILURE_CASES],
# )
# def test_create_policy_version_cli_failure_cases(
#     context, current_dir, test_case, err_type
# ):
#     policy_id = vulkan.policy.create_policy(
#         ctx=context,
#         name=test_case,
#         description="",
#     )
#     with pytest.raises(err_type):
#         _ = vulkan.policy.create_policy_version(
#             ctx=context,
#             policy_id=policy_id,
#             version_name="1",
#             repository_path=os.path.join(current_dir, test_case),
#         )


# @pytest.mark.parametrize(
#     "test_case",
#     SUCCESS_CASES,
#     ids=[x[0] for x in SUCCESS_CASES],
# )
# def test_create_policy_version_succeeds(context, current_dir, test_case):
#     policy_id = vulkan.policy.create_policy(
#         ctx=context,
#         name=test_case,
#         description="",
#     )
#     assert policy_id is not None
#     assert len(policy_id) > 0

#     policy_version_id = vulkan.policy.create_policy_version(
#         ctx=context,
#         policy_id=policy_id,
#         version_name="1",
#         repository_path=os.path.join(current_dir, test_case),
#     )
#     assert policy_version_id is not None
#     assert len(policy_version_id) > 0

