from abc import ABC, abstractmethod
from typing import Any

from .nodes import Node, TerminateNode, VulkanNodeDefinition


class Graph(ABC):

    def __init__(self, nodes: list[Node], input_schema: dict[str, type]):
        assert len(nodes) > 0, "Policy must have at least one node"
        assert all(
            isinstance(n, Node) for n in nodes
        ), "All elements must be of type Node"
        assert all(
            isinstance(k, str) and isinstance(v, type) for k, v in input_schema.items()
        ), "Input schema must be a dictionary of str -> type"

        self._nodes = nodes
        self._flattened_nodes = _flatten_nodes(nodes)
        self._node_definitions = {n.name: n.node_definition() for n in nodes}
        self._dependency_definitions = {n.name: n.node_dependencies() for n in nodes}
        # TODO: where should we validate the input schema?
        self.input_schema = input_schema

    @property
    def nodes(self) -> list[Node]:
        return self._nodes

    @property
    def flattened_nodes(self) -> list[Node]:
        return self._flattened_nodes

    @property
    def node_definitions(self) -> dict[str, VulkanNodeDefinition]:
        return self._node_definitions

    @property
    def dependency_definitions(self) -> dict[str, list[str] | None]:
        return self._dependency_definitions


def _flatten_nodes(nodes: list[Node]) -> list[Node]:
    flattened_nodes = []
    for node in nodes:
        if isinstance(node, Graph):
            flattened_nodes.extend(_flatten_nodes(node.nodes))
        else:
            flattened_nodes.append(node)
    return flattened_nodes


class Policy(Graph):
    def __init__(
        self,
        nodes: list[Node],
        input_schema: dict[str, type],
        output_callback: callable,
    ):
        assert callable(output_callback), "Output callback must be a callable"
        self.output_callback = output_callback
        nodes = self._with_output_callback(nodes)

        super().__init__(nodes, input_schema)

    def _with_output_callback(self, nodes: list[Node]) -> list[Node]:
        modified_nodes = []
        for node in nodes:
            if isinstance(node, TerminateNode):
                node = node.with_callback(self.output_callback)
            modified_nodes.append(node)

        return modified_nodes
