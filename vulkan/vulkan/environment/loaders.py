import json

from vulkan_public.core.policy import Policy
from vulkan_public.spec.policy import PolicyDefinition


SPEC_FILE_NAME = "policy.json"


def load_and_resolve_policy() -> Policy:
    with open(SPEC_FILE_NAME, "r") as f:
        spec = json.load(f)

    policy_definition = PolicyDefinition.from_dict(spec)

    policy = Policy(
        policy_definition.nodes,
        policy_definition.input_schema,
        policy_definition.output_callback,
    )
    return policy
