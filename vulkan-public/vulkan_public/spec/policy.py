from dataclasses import dataclass, field
from typing import Callable

from vulkan_public.spec.component import ComponentInstance
from vulkan_public.spec.graph import GraphDefinition
from vulkan_public.spec.nodes import Node, NodeType


@dataclass
class PolicyDefinition(GraphDefinition):
    nodes: list[Node]
    input_schema: dict[str, type]
    output_callback: Callable | None = None
    components: list[ComponentInstance] = field(default_factory=list)

    def __post_init__(self):
        if self.output_callback is not None:
            if not callable(self.output_callback):
                raise ValueError("Output callback must be a callable")

        self.validate_nodes()

        nodes = {node.name: node.dependencies for node in self.nodes}
        nodes.update({c.config.name: c.config.dependencies for c in self.components})
        self.validate_node_dependencies(nodes)

    def validate_nodes(self):
        # TODO: we should assert that all leaves are terminate nodes
        terminate_nodes = [
            node for node in self.nodes if node.type == NodeType.TERMINATE
        ]
        if len(terminate_nodes) == 0:
            raise ValueError("No terminate node found in policy.")
