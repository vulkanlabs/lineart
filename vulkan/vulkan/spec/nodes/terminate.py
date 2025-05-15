from enum import Enum
from typing import Any, Callable, cast

from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import TerminateNodeMetadata


class TerminateNode(Node):
    """Marks the end of a workflow.

    Terminate nodes are used to mark the end of a workflow.
    They signal to the engine that the workflow has finished executing,
    and can be used to return a status code or a final decision, for example.

    Additionally, the user can specify a callback that will be executed
    when the node is run. This can be used to perform cleanup tasks, for example,
    or to communicate the final result of the workflow to an external system.

    All workflows must end with a terminate node, and all leaf nodes
    must be terminate nodes.
    This is currently not enforced, but it will be in the future.
    """

    def __init__(
        self,
        name: str,
        return_status: Enum | str,
        dependencies: dict[str, Dependency],
        return_metadata: dict[str, Dependency] | None = None,
        description: str | None = None,
        callback: Callable | None = None,
        hierarchy: list[str] | None = None,
    ):
        """Marks the end of a workflow.

        Parameters
        ----------
        name : str
            The name of the node.
        return_status: Enum | str
            A "status" value that will be stored as the final status for the run.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.
        return_metadata: dict, optional
            A dictionary of metadata that will be returned by the run.
        description: str, optional
            A description of the node.
        callback: Callable, optional
            A callback that will be executed when the node is run.
            In the current implementation, the callback function always
            receives an execution context as its first argument.
            TODO: improve documentation on callback function signature.

        """
        self.return_status = (
            return_status.value if isinstance(return_status, Enum) else return_status
        )
        if dependencies is None or len(dependencies) == 0:
            raise ValueError(f"Dependencies not set for TERMINATE op {name}")
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.TERMINATE,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )
        self.callback = callback

        if return_metadata is not None:
            if not isinstance(return_metadata, dict):
                raise TypeError(
                    f"Return metadata must be a dict, got: {type(return_metadata)}"
                )
            if not all(isinstance(d, Dependency) for d in return_metadata.values()):
                raise ValueError("Return metadata values must be of type Dependency")
        self.return_metadata = return_metadata

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=TerminateNodeMetadata(
                return_status=self.return_status,
                return_metadata=self.return_metadata,
            ),
            hierarchy=self.hierarchy,
        )

    def with_callback(self, callback: Callable) -> "TerminateNode":
        self.callback = callback
        return self

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "TerminateNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.metadata is None:
            raise ValueError(f"Metadata not set for TERMINATE node {definition.name}")

        metadata = cast(TerminateNodeMetadata, definition.metadata)
        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            return_status=metadata.return_status,
            return_metadata=metadata.return_metadata,
            hierarchy=definition.hierarchy,
        )
