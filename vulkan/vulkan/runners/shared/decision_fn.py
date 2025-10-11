from typing import Any

from vulkan.node_config import normalize_to_template, resolve_template


def evaluate_condition(condition: str, inputs: dict[str, Any]) -> bool:
    norm_cond = normalize_to_template(condition)
    result = resolve_template(norm_cond, inputs, env_variables={})
    if not isinstance(result, bool):
        raise ValueError(f"Condition did not evaluate to a boolean: {condition}")
    return result
