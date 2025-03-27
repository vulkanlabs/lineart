from typing import Callable

from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.graph import GraphDefinition
from vulkan_public.spec.nodes import InputNode, Node, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition


class Policy(GraphDefinition):
    def __init__(
        self,
        nodes: list[Node],
        input_schema: dict[str, type],
        output_callback: Callable | None = None,
        hierarchy_level: str | None = None,
    ):
        if output_callback is not None:
            if not callable(output_callback):
                msg = "Output callback must be callable (a function or method)"
                raise TypeError(msg)
            nodes = self._with_output_callback(nodes)

        if not all(
            isinstance(k, str) and isinstance(v, type) for k, v in input_schema.items()
        ):
            raise TypeError("Input schema must be a dictionary of str -> type")

        all_nodes = [_make_input_node(input_schema), *nodes]
        if hierarchy_level is not None:
            all_nodes = [
                node.with_hierarchy_level(hierarchy_level) for node in all_nodes
            ]

        self.nodes = all_nodes
        self.input_schema = input_schema
        self.hierarchy_level = hierarchy_level
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


def _make_input_node(input_schema) -> InputNode:
    return InputNode(
        name=INPUT_NODE,
        description="Input node",
        schema=input_schema,
    )
