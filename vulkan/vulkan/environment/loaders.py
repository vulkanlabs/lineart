from vulkan_public.core.policy import Policy
from vulkan_public.spec.environment.loaders import (
    load_component_definition_from_alias,
    load_policy_definition,
)

from vulkan.core.component import ComponentGraph, check_all_parameters_specified


def resolve_policy(module_name: str, components_base_dir: str) -> Policy:
    policy_definition = load_policy_definition(module_name)
    components = []

    for component_instance in policy_definition.components:
        alias = component_instance.alias()
        component_definition = load_component_definition_from_alias(
            alias, components_base_dir
        )

        check_all_parameters_specified(component_definition, component_instance)
        component = ComponentGraph.from_spec(component_definition, component_instance)
        components.append(component)

    policy = Policy(
        policy_definition.nodes,
        policy_definition.input_schema,
        policy_definition.output_callback,
        components,
    )
    return policy
