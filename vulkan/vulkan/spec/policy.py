from dataclasses import dataclass, field

from vulkan.spec.component import ComponentInstance
from vulkan.spec.dependency import INPUT_NODE
from vulkan.spec.nodes import Node


@dataclass
class PolicyDefinition:
    nodes: list[Node]
    input_schema: dict[str, type]
    output_callback: callable
    components: list[ComponentInstance] = field(default_factory=list)

    def __post_init__(self):
        if not callable(self.output_callback):
            raise ValueError("Output callback must be a callable")

        self._validate_node_dependencies()

    def _validate_node_dependencies(self):
        nodes = {node.name: node.dependencies for node in self.nodes}
        nodes.update({c.config.name: c.config.dependencies for c in self.components})

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
