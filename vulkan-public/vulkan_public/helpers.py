from dagster import OpExecutionContext

from vulkan_public.constants import POLICY_CONFIG_KEY


def get_policy_config(context: OpExecutionContext) -> dict:
    config_variables = getattr(context.resources, POLICY_CONFIG_KEY)
    return config_variables.variables
