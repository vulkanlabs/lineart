from typing import Any, Callable, cast

from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import TransformNodeMetadata
from vulkan.spec.nodes.user_code import (
    UserCodeException,
    get_source_code,
    get_udf_instance,
)


class TransformNode(Node):
    """Evaluate an arbitrary function.

    Transform nodes are used to evaluate arbitrary functions.
    They can be thought of as functions, and can be used to transform
    data (hence the name), perform calculations, etc.
    At the moment, there is no limit to the type of functions that can be
    evaluated by a transform node, provided that the function is serializable.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        dependencies: dict[str, Any],
        description: str | None = None,
        hierarchy: list[str] | None = None,
        parameters: dict[str, str] | None = None,
    ):
        """Evaluate an arbitrary function.

        In the current implementation, the function always receives an
        execution context as its first argument.
        This context can be used for logging via the `ctx.log` attribute.
        Dependencies are passed as keyword arguments.
        keyword arguments, eg.:
        ```
        def add(ctx, a, b):
            ctx.logger.info(f"Adding {a} and {b}")
            return a + b

        node = TransformNode(
            name="add_node",
            func=add,
            dependencies={"a": Dependency("source_a"), "b": Dependency("source_b")},
        )
        ```

        Parameters
        ----------
        name : str
            The name of the node.
        func: callable
            An arbitrary function that will be executed when the node is run.
            The function should receive the dependencies as arguments.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.
        description: str, optional
            A description of the node.

        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.TRANSFORM,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )
        if not callable(func):
            raise TypeError(f"Expected callable, got ({type(func)})")
        self.func = func
        self.parameters = parameters

    def node_definition(self) -> NodeDefinition:
        # Get the text of source code for the user function
        source_code: str = get_source_code(self.func)

        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=TransformNodeMetadata(
                source_code=source_code,
                parameters=self.parameters,
            ),
            hierarchy=self.hierarchy,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "TransformNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.metadata is None:
            raise ValueError(f"Metadata not set for node {definition.name}")

        metadata = cast(TransformNodeMetadata, definition.metadata)

        try:
            # Load the stringified source code into a Python executable and
            # encapsulate it in a callable object.
            udf_instance: Callable = get_udf_instance(
                metadata.source_code, definition.dependencies
            )
        except UserCodeException as e:
            raise ValueError(f"Invalid user code in node {definition.name}") from e

        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            func=udf_instance,
            hierarchy=definition.hierarchy,
            parameters=metadata.parameters,
        )
