import os

from vulkan_public.spec.environment.loaders import (
    load_component_definition,
    load_policy_definition,
)
from vulkan_public.spec.environment.packing import find_package_entrypoint

from vulkan.core.component import ComponentGraph, check_all_parameters_specified
from vulkan.core.policy import Policy


def resolve_policy(file_location: str, components_base_dir: str) -> Policy:
    policy_definition = load_policy_definition(file_location)
    components = []

    for component_instance in policy_definition.components:
        alias = component_instance.alias()
        file_location = find_package_entrypoint(
            os.path.join(components_base_dir, alias)
        )
        component_definition = load_component_definition(file_location)

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
