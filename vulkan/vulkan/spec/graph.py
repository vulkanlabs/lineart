from dataclasses import dataclass
from graphlib import TopologicalSorter

import graphviz
import networkx as nx

from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes.base import Node, NodeType

GraphNodes = list[Node]
GraphEdges = dict[str, dict[str, Dependency]]
"""Mapping of node names to their dependencies"""
Dependencies = dict[str, Dependency]
"""Map of a node's input variables to dependencies on other nodes' outputs."""


@dataclass
class GraphDefinition:
    """Specifies a graph via the nodes and the dependencies between them.

    Internal convenience used to share common functionality between different
    types of graphs.
    Should not be used directly.
    """

    nodes: GraphNodes

    def __post_init__(self):
        if len(self.nodes) == 0:
            raise ValueError("Policy must have at least one node")
        if not all(isinstance(n, Node) for n in self.nodes):
            msg = f"All elements must be of type Node, got {self.nodes}"
            raise ValueError(msg)

        self._validate_nodes()
        self._validate_node_dependencies()
        self._graph = _digraph_from_nodes(self.nodes)
        valid, errors = self._validate_graph()
        self._valid = valid
        self._errors = errors

        # self._node_definitions = {n.id: n.node_definition() for n in self.nodes}
        self._dependency_definitions = {n.id: n.dependencies for n in self.nodes}

    @property
    def edges(self) -> GraphEdges:
        return self._dependency_definitions

    # @property
    # def node_definitions(self) -> dict[str, NodeDefinition]:
    #     return self._node_definitions

    @property
    def valid(self) -> bool:
        return self._valid

    @property
    def errors(self) -> list[str]:
        return self._errors

    @property
    def leaves(self) -> dict[str, Node]:
        return {
            n: self._graph.nodes[n]["node"] for n, d in self._graph.out_degree if d == 0
        }

    def _validate_node_dependencies(self):
        node_dependencies = {node.id: node.dependencies for node in self.nodes}
        for node_name, dependencies in node_dependencies.items():
            if dependencies is None:
                continue

            for dep in dependencies.values():
                if dep.node == INPUT_NODE:
                    # Input nodes are added to the graph after validation.
                    continue

                if dep.id not in node_dependencies.keys():
                    msg = (
                        f"Node {node_name} has a dependency {dep.id} "
                        "that is not in the graph"
                    )
                    raise ValueError(msg)

    def show(self):
        return nx_to_graphviz(self._graph)

    def _validate_graph(self) -> tuple[bool, list[str]]:
        errors = []
        if not nx.is_directed_acyclic_graph(self._graph):
            errors.append("Policy graph contains cycles")

        terminate_nodes = [
            node for node in self.nodes if node.type == NodeType.TERMINATE
        ]
        if len(terminate_nodes) == 0:
            errors.append("No terminate node found in policy.")

        leaves = {
            name: leaf.type == NodeType.TERMINATE for name, leaf in self.leaves.items()
        }
        if not all(leaves.values()):
            msg = f"Policy leaves must be {NodeType.TERMINATE} nodes: {leaves}"
            errors.append(msg)

        return (len(errors) == 0), errors

    def _validate_nodes(self):
        for node in self.nodes:
            if not isinstance(node, Node):
                raise ValueError("All elements must be of type `Node`")

        ids = [node.id for node in self.nodes]
        duplicates = set([node_id for node_id in ids if ids.count(node_id) > 1])

        if duplicates:
            raise ValueError(f"Duplicate node names found: {duplicates}")


def nx_to_graphviz(G, prog="dot"):
    """
    Convert a NetworkX DiGraph to a Graphviz visualization
    Parameters:
    - G: NetworkX DiGraph
    - prog: Graphviz layout program ('dot', 'neato', 'fdp', 'sfdp', 'twopi', 'circo')
    Returns:
    - Graphviz object
    """
    # Create a new Graphviz Digraph
    dot = graphviz.Digraph(engine=prog)

    # Add nodes
    for node in G.nodes():
        # Get node attributes if any
        attrs = G.nodes[node]
        # Convert all attribute values to strings
        attrs = {k: str(v) for k, v in attrs.items()}
        dot.node(str(node), **attrs)

    # Add edges
    for u, v in G.edges():
        # Get edge attributes if any
        attrs = G.edges[u, v]
        # Convert all attribute values to strings
        attrs = {k: str(v) for k, v in attrs.items()}
        dot.edge(str(u), str(v), **attrs)

    return dot


def _digraph_from_nodes(nodes: list[Node]) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_nodes_from([(n.id, {"node": n}) for n in nodes])

    edges: list[tuple[str, str, dict]] = []
    for node in nodes:
        for dep_name, dep_node in node.dependencies.items():
            properties = {
                "dependency_name": dep_name,
                "source_node_name": dep_node.node,
                "source_node_output": dep_node.output,
                "source_node_key": dep_node.key,
                "source_node_hierarchy": dep_node.hierarchy,
            }
            e = (dep_node.id, node.id, properties)
            edges.append(e)

    g.add_edges_from(edges)
    return g


def extract_node_definitions(nodes: list[Node]) -> dict:
    return {node.id: node.to_dict() for node in nodes}


def sort_nodes(nodes: GraphNodes, edges: GraphEdges) -> GraphNodes:
    """Sort nodes topologically based on their dependencies."""
    node_map = {node.id: node for node in nodes}
    graph = {
        _id: [dep.id for dep in dependencies.values()]
        for _id, dependencies in edges.items()
    }
    sorter = TopologicalSorter(graph)

    # Input nodes may not be included in the nodes list, but will be
    # referenced as dependencies in the edges list.
    return [node_map[_id] for _id in sorter.static_order() if _id in node_map]
