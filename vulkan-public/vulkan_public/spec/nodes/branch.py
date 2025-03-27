from inspect import getsource
from typing import Any, Callable, cast

from vulkan_public.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan_public.spec.nodes.metadata import BranchNodeMetadata
from vulkan_public.spec.nodes.user_code import get_udf_instance


class BranchNode(Node):
    """Perform branching logic in the DAG.

    Branch nodes are used to evaluate arbitrary functions, and use the
    result to determine the next steps in the workflow.
    Branching is exclusive, meaning that only one of the possible output
    branches will be selected per execution.

    Any function can be used to evaluate the branching logic.
    All outputs of the function must be strings, which will be used to
    identify the possible branches.
    It is necessary to specify all possible outputs of the function when
    creating the node.

    At the moment, there is no limit to the type of functions that can be
    evaluated by a branch node, provided that the function is serializable.
    """

    def __init__(
        self,
        name: str,
        func: Callable | str,
        choices: list[str],
        dependencies: dict[str, Any],
        description: str | None = None,
    ):
        """Perform branching logic in the DAG.

        In the current implementation, the function always receives an
        execution context as its first argument.
        This context can be used for logging via the `ctx.log` attribute.

        Parameters
        ----------
        name : str
            The name of the node.
        func: callable
            An arbitrary function that will be executed when the node is run.
            The function should receive the dependencies as arguments.
            All return values of the function should be strings matching one of
            the values in the `outputs` parameter.
        choices: list[str]
            The possible outputs of the function.
            Represents the possible branches of the node.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.
        description: str, optional
            A description of the node.

        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.BRANCH,
            dependencies=dependencies,
        )

        if choices is None or len(choices) == 0:
            raise ValueError("BranchNode must have at least one possible output")
        self.choices = choices

        if callable(func):
            self.func = func
            self.user_code = getsource(func)
        elif isinstance(func, str):
            self.user_code = func
            udf_instance = get_udf_instance(func)
            self.func = udf_instance
        else:
            raise TypeError(
                f"`func` should be a function or function declaration, got {type(func)}"
            )

        # TODO: we can likely use the AST to check if the given function
        # returns a string, and if it has the correct outputs, ie covers
        # all possible choices.

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=BranchNodeMetadata(
                choices=self.choices,
                source=self.user_code,
            ),
        )

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "BranchNode":
        definition = NodeDefinition.from_dict(spec)

        if definition.metadata is None:
            raise ValueError(f"Metadata not set for node {definition.name}")

        metadata = cast(BranchNodeMetadata, definition.metadata)
        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            func=metadata.source,
            choices=metadata.choices,
        )
