import json

from vulkan.core.policy import Policy
from vulkan.exceptions import (
    ConflictingDefinitionsError,
    DefinitionNotFoundException,
    InvalidDefinitionError,
    UserImportException,
)
from vulkan.spec.environment.packing import find_definitions
from vulkan.spec.policy import PolicyDefinition


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


def load_and_resolve_policy(spec_file_path: str) -> Policy:
    with open(spec_file_path, "r") as f:
        spec = json.load(f)

    policy_definition = PolicyDefinition.from_dict(spec)

    policy = Policy.from_definition(policy_definition)
    return policy
