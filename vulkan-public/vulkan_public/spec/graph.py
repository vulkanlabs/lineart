from dataclasses import dataclass

from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes.base import Node

Dependencies = dict[str, Dependency]
"""Map of a node's input variables to dependencies on other nodes' outputs."""
NodeDependencies = dict[str, Dependencies]
"""Map of node names to their dependencies."""


@dataclass
class GraphDefinition:
    """Specifies a graph via the nodes and the dependencies between them.

    Internal convenience used to share common functionality between different
    types of graphs.
    Should not be used directly.
    """

    nodes: list[Node]

    def __post_init__(self):
        self._validate_nodes(self.nodes)

    def _validate_nodes(nodes: list[Node]):
        for node in nodes:
            if not isinstance(node, Node):
                raise ValueError("All elements must be of type `Node`")

            if node.name == INPUT_NODE:
                raise ValueError(f"Node name `{INPUT_NODE}` is reserved")

        names = [node.name for node in nodes]
        duplicates = set([name for name in names if names.count(name) > 1])

        if duplicates:
            raise ValueError(f"Duplicate node names found: {duplicates}")

    @staticmethod
    def validate_node_dependencies(node_dependencies: NodeDependencies):
        for node_name, dependencies in node_dependencies.items():
            if dependencies is None:
                continue

            for dep in dependencies.values():
                if dep.node == INPUT_NODE:
                    # Input nodes are added to the graph after validation.
                    continue

                if dep.node not in node_dependencies.keys():
                    msg = (
                        f"Node {node_name} has a dependency {dep.node} "
                        "that is not in the graph"
                    )
                    raise ValueError(msg)
