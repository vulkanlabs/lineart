from vulkan_public.core.policy import Policy
from vulkan_public.spec.environment.loaders import load_policy_definition


def resolve_policy(module_name: str) -> Policy:
    policy_definition = load_policy_definition(module_name)
    components = []

    policy = Policy(
        policy_definition.nodes,
        policy_definition.input_schema,
        policy_definition.output_callback,
        components,
    )
    return policy
