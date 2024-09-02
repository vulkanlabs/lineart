from abc import ABC

from .dependency import Dependency
from .nodes import Node, NodeType, VulkanNodeDefinition


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
        self._flattened_dependencies = _flatten_dependencies(nodes)
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

    @property
    def flattened_dependencies(self) -> dict[str, list[str] | None]:
        return self._flattened_dependencies


def _flatten_dependencies(nodes: list[Node]) -> dict[str, list[Dependency]]:
    all_nodes = {node.name: node for node in nodes}
    flattened_dependencies = {}

    # Flatten nodes without discarding component nodes
    for node in nodes:
        if node.type == NodeType.COMPONENT:
            for component_node in node.nodes:
                flattened_dependencies[component_node.name] = (
                    component_node.dependencies
                )
                all_nodes[component_node.name] = component_node

    for node in nodes:
        if node.type == NodeType.COMPONENT:
            # Components are treated as "virtual" nodes at the moment
            continue

        dependencies = {}
        for name, dependency in node.dependencies.items():
            if dependency.node not in all_nodes.keys():
                # This handles the case of the input node, which is only
                # inserted by upper layers.
                # When we remodel core as a config/spec, we can refactor
                dependencies[name] = dependency
                continue

            # TODO: bring this valitation to PolicyDefinition
            dep_node: Node = all_nodes[dependency.node]
            if dep_node.type == NodeType.TERMINATE:
                raise ValueError(
                    f"Node {node.name} depends on terminate node {dependency}"
                )

            if dep_node.type == NodeType.COMPONENT:
                dependency.node = dep_node.output_node_name

            dependencies[name] = dependency

        flattened_dependencies[node.name] = dependencies

    return flattened_dependencies


def _flatten_nodes(nodes: list[Node]) -> list[Node]:
    flattened_nodes = []
    for node in nodes:
        if isinstance(node, Graph):
            flattened_nodes.extend(_flatten_nodes(node.nodes))
        else:
            flattened_nodes.append(node)
    return flattened_nodes
