from typing import Callable

from vulkan.core.resolution import resolve
from vulkan.spec.graph import GraphDefinition
from vulkan.spec.nodes import Node, TerminateNode
from vulkan.spec.policy import PolicyDefinition


class Policy(GraphDefinition):
    def __init__(
        self,
        nodes: list[Node],
        output_callback: Callable | None = None,
        hierarchy_level: str | None = None,
    ):
        if output_callback is not None:
            if not callable(output_callback):
                msg = "Output callback must be callable (a function or method)"
                raise TypeError(msg)
            nodes = self._with_output_callback(nodes, output_callback)

        resolved_nodes = resolve(nodes)

        self.hierarchy_level = hierarchy_level
        self.nodes = resolved_nodes
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

        all_nodes = [definition.input_node, *definition.nodes]

        return cls(
            nodes=all_nodes,
            output_callback=definition.output_callback,
            hierarchy_level=hierarchy_level,
        )
