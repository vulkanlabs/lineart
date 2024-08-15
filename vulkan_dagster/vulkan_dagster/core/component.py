from dataclasses import dataclass
from typing import Any

from .nodes import Node, NodeType, TransformNode, VulkanNodeDefinition
from .graph import Graph


class ComponentGraph(Node, Graph):

    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        dependencies: dict[str, Any],
    ):
        # TODO: match input_schema with dependencies
        # TODO: assert there aren't Terminate nodes in the component

        # TODO: insert component input node as internal node (when we have
        # the execution logic implemented in our core)

        Node.__init__(self, name, description, NodeType.COMPONENT, dependencies)
        Graph.__init__(self, nodes, input_schema)

    @property
    def input_node_name(self) -> str:
        return self.make_input_node_name(self.name)
    
    @property
    def output_node_name(self) -> str:
        return self.make_output_node_name(self.name)
    
    @staticmethod
    def make_input_node_name(component_name: str) -> str:
        return f"{component_name}_input"
    
    @staticmethod
    def make_output_node_name(component_name: str) -> str:
        return f"{component_name}_output"

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.node_dependencies(),
            metadata={
                "nodes": {n.name: n.node_definition() for n in self.nodes},
            },
        )
