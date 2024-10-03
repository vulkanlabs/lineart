from dataclasses import dataclass

from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import Node

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

    @staticmethod
    def validate_node_dependencies(nodes: NodeDependencies):
        for node_name, dependencies in nodes.items():
            if dependencies is None:
                continue

            for dep in dependencies.values():
                if dep.node == INPUT_NODE:
                    # Input nodes are added to the graph after validation.
                    continue

                if dep.node not in nodes.keys():
                    msg = (
                        f"Node {node_name} has a dependency {dep.node} "
                        "that is not in the graph"
                    )
                    raise ValueError(msg)
