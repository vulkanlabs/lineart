import os

from vulkan.exceptions import (
    ConflictingDefinitionsError,
    DefinitionNotFoundException,
    InvalidDefinitionError,
)
from vulkan.spec.component import ComponentDefinition
from vulkan.spec.environment.packing import find_definitions, find_package_entrypoint
from vulkan.spec.policy import PolicyDefinition


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