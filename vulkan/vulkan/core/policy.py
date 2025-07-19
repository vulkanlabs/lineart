import builtins
from typing import Callable

from vulkan.spec.dependency import INPUT_NODE
from vulkan.spec.graph import GraphDefinition
from vulkan.spec.nodes import InputNode, Node, TerminateNode
from vulkan.spec.policy import PolicyDefinition


class Policy(GraphDefinition):
    def __init__(
        self,
        nodes: list[Node],
        input_schema: dict[str, type | str],
        output_callback: Callable | None = None,
        hierarchy_level: str | None = None,
    ):
        if output_callback is not None:
            if not callable(output_callback):
                msg = "Output callback must be callable (a function or method)"  # noqa: B904
                raise TypeError(msg)
            nodes = self._with_output_callback(nodes, output_callback)

        input_schema = _parse_input_schema(input_schema)

        # TODO: add the resolution step here.
        all_nodes = [_make_input_node(input_schema), *nodes]

        # TODO: ensure that the hierarchy is correctly created.
        if hierarchy_level is not None:
            all_nodes = [
                node.add_hierarchy_level(hierarchy_level) for node in all_nodes
            ]

        self.hierarchy_level = hierarchy_level
        self.nodes = all_nodes
        self.input_schema = input_schema
        self.output_callback = output_callback
        super().__post_init__()

    def _with_output_callback(
        self, nodes: list[Node], output_callback: Callable
    ) -> list[Node]:
        modified_nodes = []
        for node in nodes:
            if isinstance(node, TerminateNode):
                node = node.with_callback(output_callback)
            modified_nodes.append(node)

        return modified_nodes

    @classmethod
    def from_definition(
        cls,
        definition: PolicyDefinition,
        hierarchy_level: str | None = None,
    ) -> "Policy":
        if not definition.valid:
            msg = f"Policy definition is not valid: {definition.errors}"
            raise ValueError(msg)

        return cls(
            nodes=definition.nodes,
            input_schema=definition.input_schema,
            output_callback=definition.output_callback,
            hierarchy_level=hierarchy_level,
        )


def _parse_input_schema(input_schema: dict[str, type | str]) -> dict[str, type | str]:
    """Parse the input schema to ensure that all types are valid."""
    parsed_schema = {}
    for key, value in input_schema.items():
        if isinstance(value, str):
            # If the type is a string, we assume it's a built-in type
            if hasattr(builtins, value):
                parsed_schema[key] = getattr(builtins, value)
            else:
                msg = f"Invalid type '{value}' for key '{key}'"
                raise ValueError(msg)
        elif isinstance(value, type):
            parsed_schema[key] = value
        else:
            msg = f"Invalid type for key '{key}': {type(value)}"
            raise ValueError(msg)
    return parsed_schema


def _make_input_node(input_schema) -> InputNode:
    return InputNode(
        name=INPUT_NODE,
        description="Input node",
        schema=input_schema,
    )
