import os

from vulkan.core.component import ComponentGraph, check_all_parameters_specified
from vulkan.core.exceptions import (
    DefinitionNotFoundException,
    InvalidDefinitionError,
    ConflictingDefinitionsError,
)
from vulkan.core.policy import Policy
from vulkan.environment.packing import find_definitions, find_package_entrypoint
from vulkan.spec.component import ComponentDefinition
from vulkan.spec.policy import PolicyDefinition


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


def load_policy_definition(file_location: str) -> PolicyDefinition:
    try:
        definitions = find_definitions(file_location, PolicyDefinition)
    except Exception as e:
        raise InvalidDefinitionError(e)

    if len(definitions) == 0:
        raise DefinitionNotFoundException("Failed to load the PolicyDefinition")

    if len(definitions) > 1:
        raise ConflictingDefinitionsError(
            f"Expected only one PolicyDefinition in the module, found {len(definitions)}"
        )
    return definitions[0]


def load_component_definition_from_alias(
    alias: str, components_base_dir: str
) -> ComponentDefinition:
    file_location = find_package_entrypoint(os.path.join(components_base_dir, alias))
    return load_component_definition(file_location)


def load_component_definition(file_location: str) -> ComponentDefinition:
    definitions = find_definitions(file_location, ComponentDefinition)
    if len(definitions) != 1:
        raise ValueError(
            f"Expected only one ComponentDefinition in the module, found {len(definitions)}"
        )
    return definitions[0]
