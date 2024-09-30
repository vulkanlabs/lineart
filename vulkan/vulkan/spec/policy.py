from dataclasses import dataclass, field

from vulkan.spec.component import ComponentInstance
from vulkan.spec.graph import GraphDefinition
from vulkan.spec.nodes import Node


@dataclass
class PolicyDefinition(GraphDefinition):
    nodes: list[Node]
    input_schema: dict[str, type]
    output_callback: callable
    components: list[ComponentInstance] = field(default_factory=list)

    def __post_init__(self):
        if not callable(self.output_callback):
            raise ValueError("Output callback must be a callable")

        nodes = {node.name: node.dependencies for node in self.nodes}
        nodes.update({c.config.name: c.config.dependencies for c in self.components})
        self.validate_node_dependencies(nodes)
