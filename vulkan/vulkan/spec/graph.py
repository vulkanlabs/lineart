from dataclasses import dataclass

from vulkan.spec.dependency import INPUT_NODE
from vulkan.spec.nodes import Node


@dataclass
class GraphDefinition:
    nodes: list[Node]

    def validate_node_dependencies(self):
        nodes = {node.name: node.dependencies for node in self.nodes}

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
