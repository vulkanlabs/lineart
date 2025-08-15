from typing import Any

from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import ComponentNodeMetadata


class ComponentNode(Node):
    """A node that represents a component."""

    def __init__(
        self,
        name: str,
        component_name: str,
        definition: dict | None = None,
        description: str | None = None,
        dependencies: dict[str, Dependency] | None = None,
        parameters: dict | None = None,
    ):
        """A node that represents a component.

        Component nodes are used to "invoke" components from within workflows.
        They're used to insert additional metadata for the component so that it
        can be appropriately connected to the rest of the workflow.

        Parameters
        ----------
        name : str
            The name of the node.
        component_id : str
            The ID of the component to invoke.
        definition : dict, optional
            The definition of the component to invoke.
        description : str, optional
            A description of the node. Used for documentation purposes and
            shown in the user interface.
        dependencies : dict, optional
            The dependencies of the node.
            See `Dependency` for more information.
        parameters : dict, optional
            A dictionary of runtime parameters to be passed to the component.
            These parameters can be used to customize the component invocation.
        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.COMPONENT,
            dependencies=dependencies,
        )
        self.component_name = component_name
        self.definition = definition
        self.parameters = parameters or {}

    def node_definition(self) -> NodeDefinition:
        metadata = ComponentNodeMetadata(
            component_name=self.component_name,
            definition=self.definition,
            parameters=self.parameters,
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
        if node.metadata is None or node.metadata.component_name is None:
            raise ValueError("Missing component metadata")

        return cls(
            name=node.name,
            description=node.description,
            dependencies=node.dependencies,
            component_name=node.metadata.component_name,
            definition=node.metadata.definition,
            parameters=node.metadata.parameters,
        )
