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

    def node_definition(self) -> NodeDefinition:
        metadata = ComponentNodeMetadata(component_id=self.component_id)
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=metadata,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "ComponentNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.node_type != NodeType.COMPONENT.value:
            raise ValueError(f"Expected NodeType.COMPONENT, got {definition.node_type}")
        if definition.metadata is None or definition.metadata.component_id is None:
            raise ValueError("Missing component metadata")

        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            component_id=definition.metadata.component_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "node_type": self.type.value,
            "description": self.description,
            "dependencies": self.dependencies,
            "metadata": {
                "component_id": self.component_id,
            },
        }
