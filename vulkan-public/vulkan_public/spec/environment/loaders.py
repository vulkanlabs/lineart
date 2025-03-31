from vulkan_public.exceptions import (
    ConflictingDefinitionsError,
    DefinitionNotFoundException,
    InvalidDefinitionError,
    UserImportException,
)
from vulkan_public.spec.environment.packing import find_definitions
from vulkan_public.spec.policy import PolicyDefinition


def load_single_definition(module_name: str, definition_type: type):
    try:
        definitions = find_definitions(module_name, definition_type)
    except ModuleNotFoundError as e:
        raise UserImportException(str(e))
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


def load_policy_definition(module_name: str) -> PolicyDefinition:
    return load_single_definition(module_name, PolicyDefinition)
