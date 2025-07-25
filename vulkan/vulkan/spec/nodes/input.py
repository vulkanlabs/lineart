from typing import Any, cast

from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import InputNodeMetadata


class InputNode(Node):
    """The first node in a workflow.

    Input nodes are used to define the input schema of a workflow.
    They are used to validate the input data, and to provide a way for the user
    to pass data to the workflow.

    Input nodes are always the first node in any policy or component.
    They are added by the engine, and should not be declared by the user.
    """

    def __init__(
        self,
        schema: dict[str, type],
        name="input_node",
        description: str | None = None,
        hierarchy: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            typ=NodeType.INPUT,
            description=description,
            dependencies=None,
            hierarchy=hierarchy,
        )
        self.schema = schema

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            metadata=InputNodeMetadata(
                schema={k: t.__name__ for k, t in self.schema.items()}
            ),
            hierarchy=self.hierarchy,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "InputNode":
        definition = NodeDefinition.from_dict(spec)
        metadata = cast(InputNodeMetadata, definition.metadata)
        schema = parse_input_schema(metadata.schema)
        return cls(
            schema=schema,
            name=definition.name,
            description=definition.description,
            hierarchy=definition.hierarchy,
        )

    def with_dependencies(self, dependencies: dict[str, Dependency]) -> "InputNode":
        self._dependencies = dependencies
        return self


def parse_input_schema(schema: dict[str, str]) -> dict[str, type]:
    """Parse a schema dictionary into a dictionary of types.

    Args:
        schema (dict[str, str]): A dictionary of field names and their types.

    Returns:
        dict[str, type]: A dictionary of field names and their types.
    """
    parsed_schema = {}
    for key, value in schema.items():
        try:
            parsed_schema[key] = _SUPPORTED_TYPES[value]
        except KeyError as e:
            raise ValueError(f"Unsupported type {value} for field {key}") from e
    return parsed_schema


_SUPPORTED_TYPES = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    # "list": list,
    # "dict": dict,
    # "tuple": tuple,
    # "set": set,
}
