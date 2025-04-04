from inspect import getsource
from typing import Any, Callable, cast

from vulkan_public.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan_public.spec.nodes.metadata import TransformNodeMetadata
from vulkan_public.spec.nodes.user_code import UserCodeException, get_udf_instance


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
        dependencies: dict[str, Any],
        func: Callable | None = None,
        source_code: str | None = None,
        description: str | None = None,
        hierarchy: list[str] | None = None,
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
        if func is None and source_code is None:
            raise ValueError("TransformNode must have a function or source code")
        if func is not None and source_code is not None:
            raise ValueError(
                "TransformNode cannot have both a function and source code"
            )

        if source_code is not None:
            if not isinstance(source_code, str):
                msg = f"Expected source code as string, got ({type(source_code)})"
                raise TypeError(msg)

            try:
                udf_instance = get_udf_instance(source_code)
            except UserCodeException as e:
                raise ValueError(f"Invalid user code in node {name}") from e
            self.func = udf_instance
            self.user_func = None
            self.source_code = source_code
            self.function_code = source_code

        if func is not None:
            if not callable(func):
                msg = f"Expected callable, got ({type(func)})"
                raise TypeError(msg)

            self.func = func
            self.user_func = func
            self.source_code = None
            self.function_code = getsource(func)

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=TransformNodeMetadata(
                source_code=self.source_code,
                func=self.user_func,
                function_code=self.function_code,
            ),
            hierarchy=self.hierarchy,
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "TransformNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.metadata is None:
            raise ValueError(f"Metadata not set for node {definition.name}")

        metadata = cast(TransformNodeMetadata, definition.metadata)
        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            func=metadata.func,
            source_code=metadata.source_code,
            hierarchy=definition.hierarchy,
        )
