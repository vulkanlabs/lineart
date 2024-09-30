import os

from vulkan.exceptions import (
    ConflictingDefinitionsError,
    DefinitionNotFoundException,
    InvalidDefinitionError,
)
from vulkan.spec.component import ComponentDefinition
from vulkan.spec.environment.packing import find_definitions, find_package_entrypoint
from vulkan.spec.policy import PolicyDefinition


def load_single_definition(file_location: str, definition_type: type):
    try:
        definitions = find_definitions(file_location, definition_type)
    except Exception as e:
        raise InvalidDefinitionError(e)

    if len(definitions) == 0:
        raise DefinitionNotFoundException(
            f"Failed to load the {definition_type.__name__}"
        )

    if len(definitions) > 1:
        raise ConflictingDefinitionsError(
            f"Expected only one {definition_type.__name__} in the module, "
            f"found {len(definitions)}"
        )
    return definitions[0]


def load_policy_definition(file_location: str) -> PolicyDefinition:
    return load_single_definition(file_location, PolicyDefinition)


def load_component_definition_from_alias(
    alias: str, components_base_dir: str
) -> ComponentDefinition:
    file_location = find_package_entrypoint(os.path.join(components_base_dir, alias))
    return load_component_definition(file_location)


def load_component_definition(file_location: str) -> ComponentDefinition:
    return load_single_definition(file_location, ComponentDefinition)
