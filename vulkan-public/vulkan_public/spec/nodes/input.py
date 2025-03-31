from typing import Any

from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan_public.spec.nodes.metadata import InputNodeMetadata


class InputNode(Node):
    """The first node in a workflow.

    Input nodes are used to define the input schema of a workflow.
    They are used to validate the input data, and to provide a way for the user
    to pass data to the workflow.

    Input nodes are always the first node in any policy or component.
    They are added by the engine, and should not be declared by the user.
    """

    def __init__(
        self,
        schema: dict[str, type],
        name="input_node",
        description: str | None = None,
        hierarchy: list[str] | None = None,
    ):
        super().__init__(
            name=name,
            typ=NodeType.INPUT,
            description=description,
            dependencies=None,
            hierarchy=hierarchy,
        )
        self.schema = schema

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            metadata=InputNodeMetadata(
                schema={k: t.__name__ for k, t in self.schema.items()}
            ),
            hierarchy=self.hierarchy,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "InputNode":
        definition = NodeDefinition.from_dict(spec)
        return cls(
            # FIXME: shouldnt be using eval here
            schema={k: eval(t) for k, t in definition.metadata.schema.items()},
            name=definition.name,
            description=definition.description,
            hierarchy=definition.hierarchy,
        )

    def with_dependencies(self, dependencies: dict[str, Dependency]) -> "InputNode":
        self._dependencies = dependencies
        return self
