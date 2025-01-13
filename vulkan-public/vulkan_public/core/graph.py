from abc import ABC
from copy import deepcopy
from graphlib import TopologicalSorter

from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes import Node, NodeType, VulkanNodeDefinition

GraphNodes = list[Node]
GraphEdges = dict[str, dict[str, Dependency]]
"""Mapping of node names to their dependencies"""


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
        self._flattened_nodes = flatten_nodes(nodes)
        self._node_definitions = {n.name: n.node_definition() for n in nodes}
        self._dependency_definitions = {n.name: n.node_dependencies() for n in nodes}
        self._flattened_dependencies = {
            node.name: node.dependencies for node in self._flattened_nodes
        }
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


def flatten_nodes(nodes: list[Node]) -> list[Node]:
    """Get a flattened list of nodes, where component nodes are expanded.

    Extract the inner nodes of components and update the dependencies of
    upper level nodes to reflect the flattened structure. Nodes of type
    `NodeType.COMPONENT` are ignored in the flattened list.
    """
    all_nodes = {node.name: node for node in nodes}
    flattened_nodes = []

    # Flatten nodes without discarding component nodes
    for node in nodes:
        if node.type == NodeType.COMPONENT:
            for component_node in node.nodes:
                all_nodes[component_node.name] = component_node

    for node in all_nodes.values():
        if node.type == NodeType.COMPONENT:
            # Components are treated as "virtual" nodes
            continue

        _node = deepcopy(node)

        for dependency in _node.dependencies.values():
            dep_node = all_nodes.get(dependency.node)

            if dep_node is None:
                # Skip dependencies on nodes that are automatically
                # inserted by upper layers (e.g. input nodes)
                continue

            if dep_node.type == NodeType.COMPONENT:
                # Point dependency to the component's output node
                dependency.node = dep_node.output_node_name

        flattened_nodes.append(_node)

    return flattened_nodes


def extract_node_definitions(nodes: list[Node]) -> dict:
    return {node.name: _to_dict(node.node_definition()) for node in nodes}


def _to_dict(node: VulkanNodeDefinition):
    node_ = node.__dict__.copy()
    if node.node_type == NodeType.COMPONENT.value:
        node_["metadata"]["nodes"] = {
            name: _to_dict(n) for name, n in node.metadata["nodes"].items()
        }
    return node_


def sort_nodes(nodes: GraphNodes, edges: GraphEdges) -> GraphNodes:
    """Sort nodes topologically based on their dependencies."""
    nodes = {node.name: node for node in nodes}
    graph = {
        name: [dep.node for dep in dependencies.values()]
        for name, dependencies in edges.items()
    }
    sorter = TopologicalSorter(graph)

    # Input nodes may not be included in the nodes list, but will be
    # referenced as dependencies in the edges list.
    return [nodes[name] for name in sorter.static_order() if name in nodes]
