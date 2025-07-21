from typing import Any

from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import ComponentNodeMetadata


class ComponentNode(Node):
    """A node that represents a component.
    Component nodes are used to "invoke" components from within workflows.
    They're used to insert additional metadata for the component so that it
    can be appropriately connected to the rest of the workflow.
    """

    def __init__(
        self,
        name: str,
        component_id: str,
        definition: dict | None = None,
        description: str | None = None,
        dependencies: dict[str, Dependency] | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.COMPONENT,
            dependencies=dependencies,
        )
        self.component_id = component_id
        self.definition = definition

    def node_definition(self) -> NodeDefinition:
        metadata = ComponentNodeMetadata(
            component_id=self.component_id,
            definition=self.definition,
        )
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=metadata,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "ComponentNode":
        node = NodeDefinition.from_dict(spec)
        if node.node_type != NodeType.COMPONENT.value:
            raise ValueError(f"Expected NodeType.COMPONENT, got {node.node_type}")
        if node.metadata is None or node.metadata.component_id is None:
            raise ValueError("Missing component metadata")

        return cls(
            name=node.name,
            description=node.description,
            dependencies=node.dependencies,
            component_id=node.metadata.component_id,
            definition=node.metadata.definition,
        )
