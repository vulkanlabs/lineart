import json

from vulkan.core.policy import Policy
from vulkan.spec.policy import PolicyDefinition


def load_and_resolve_policy(spec_file_path: str) -> Policy:
    with open(spec_file_path, "r") as f:
        spec = json.load(f)

    policy_definition = PolicyDefinition.from_dict(spec)

    policy = Policy.from_definition(policy_definition)
    return policy
