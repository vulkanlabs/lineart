from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from inspect import getsource
from typing import Any, Callable

from vulkan_public.spec.dependency import Dependency


class NodeType(Enum):
    TRANSFORM = "TRANSFORM"
    TERMINATE = "TERMINATE"
    CONNECTION = "CONNECTION"
    COMPONENT = "COMPONENT"
    BRANCH = "BRANCH"
    INPUT = "INPUT"
    MAP = "MAP"
    COLLECT = "COLLECT"
    DATA_INPUT = "DATA_INPUT"


@dataclass
class VulkanNodeDefinition:
    "Internal representation of a node."

    name: str
    node_type: str
    hidden: bool = False
    description: str | None = None
    dependencies: dict[str, Dependency] | None = None
    metadata: dict[str, Any] | None = None


class Node(ABC):
    """A node represents a step in a workflow.

    It can be thought of as a function that executes in an isolated environment.
    Each node represents a vertice in a DAG, and declares its dependencies,
    which are the edges in the graph.
    """

    def __init__(
        self,
        name: str,
        typ: NodeType,
        hidden: bool = False,
        description: str | None = None,
        dependencies: dict[str, Dependency] | None = None,
    ):
        """A node. This is an abstract class and should not be instantiated directly.

        Parameters
        ----------
        name : str
            The name of the node.
        typ : NodeType
            The type of the node. Determines the overall behavior of the node.
        hidden : bool, optional, default=False
            Whether the node should be hidden from the user interface.
            Mainly for internal use.
        description : str, optional
            A description of the node. Used for documentation purposes and
            shown in the user interface.
        dependencies : dict[str, Dependency], optional
            The dependencies of the node. A dictionary where the key is the name
            of the variable that will receive the data, and the value is the source.
            See `Dependency` for more information.

        """
        self._name = name
        self.description = description
        self.type = typ
        self.hidden = hidden
        self._dependencies = dependencies if dependencies is not None else {}
        # TODO: here, we can enforce the typing of dependency specifications,
        # but this ends up making the API harder to use. We should consider
        # parsing the dependency specification from strings or tuples.
        assert all(
            isinstance(d, Dependency) for d in self._dependencies.values()
        ), "Dependencies must be of type Dependency"

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> dict[str, Dependency]:
        return self._dependencies

    @abstractmethod
    def node_definition(self) -> VulkanNodeDefinition:
        pass

    def node_dependencies(self) -> list[Dependency]:
        return list(self.dependencies.values())


class HTTPConnectionNode(Node):
    """Makes an HTTP request.

    This node is used to make HTTP requests to external services.
    It can be used to fetch data from an API, send data to a webhook, etc.
    It supports all HTTP methods, and allows the user to specify headers
    and query parameters during configuration time.
    """

    def __init__(
        self,
        name: str,
        url: str,
        method: str,
        headers: dict,
        params: dict | None = None,
        description: str | None = None,
        dependencies: dict | None = None,
    ):
        """Makes an HTTP request.

        In the current implementation, `dependencies` should define a single
        key, named "body", which will be used as the body of the request, eg.:
        ```
        node = HTTPConnectionNode(
            name="http_node",
            url="https://api.example.com",
            method="POST",
            headers={"Content-Type": "application/json"},
            params={"key": "value"},
            dependencies={"body": Dependency("source_node")},
        )
        ```

        Parameters
        ----------
        name : str
            The name of the node.
        url: str
            The URL against which the request will be performed.
        method: str
            HTTP method of the request.
            Must be one of "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD".
        headers: dict
            Request headers.
        params: dict, optional
            Parameters passed as query parameters in the request.
        description: str, optional
            A description of the node. Used for documentation purposes and
            shown in the user interface.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.

        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.CONNECTION,
            dependencies=dependencies,
        )
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params if params is not None else {}

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.node_dependencies(),
            metadata={
                "url": self.url,
                "method": self.method,
                "headers": self.headers,
                "params": self.params,
            },
        )


class DataInputNode(Node):
    """A node that represents an input data source.

    Data input nodes are used to fetch data from external systems and pass
    it to the rest of the workflow.
    """

    def __init__(
        self,
        name: str,
        source: str,
        description: str | None = None,
        dependencies: dict | None = None,
    ):
        """Fetches data from a pre-configured data source.

        Parameters
        ----------
        name : str
            The name of the node.
        source: str
            The name of the configured data source.
        description: str, optional
            A description of the node. Used for documentation purposes and
            shown in the user interface.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.

        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.DATA_INPUT,
            dependencies=dependencies,
        )
        self.source = source

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.node_dependencies(),
            metadata={
                "data_source": self.source,
            },
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
        func: callable,
        dependencies: dict[str, Any],
        description: str | None = None,
        hidden: bool = False,
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
        hidden: bool, optional, default=False
            Whether the node should be hidden from the user interface.
            Mainly for internal use.

        """
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.TRANSFORM,
            dependencies=dependencies,
            hidden=hidden,
        )
        self.func = func

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            hidden=self.hidden,
            dependencies=self.node_dependencies(),
            metadata={
                "source": getsource(self.func),
            },
        )


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
        return_status: str,
        dependencies: dict[str, Any],
        description: str | None = None,
        callback: Callable | None = None,
    ):
        """Marks the end of a workflow.

        Parameters
        ----------
        name : str
            The name of the node.
        return_status: str
            A "status" value that will be stored as the final status for the run.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.
        description: str, optional
            A description of the node.
        callback: Callable, optional
            A callback that will be executed when the node is run.
            In the current implementation, the callback function always
            receives an execution context as its first argument.
            TODO: improve documentation on callback function signature.

        """
        self.return_status = return_status
        assert dependencies is not None, f"Dependencies not set for TERMINATE op {name}"
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.TERMINATE,
            dependencies=dependencies,
        )
        self.callback = callback

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.node_dependencies(),
            metadata={
                "return_status": self.return_status.value,
            },
        )

    def with_callback(self, callback: callable) -> "TerminateNode":
        self.callback = callback
        return self


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
        func: callable,
        outputs: list[str],
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
        outputs: list[str]
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
        self.func = func
        self.outputs = outputs

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.node_dependencies(),
            metadata={
                "choices": self.outputs,
                "source": getsource(self.func),
            },
        )


class InputNode(Node):
    """The first node in a workflow.

    Input nodes are used to define the input schema of a workflow.
    They are used to validate the input data, and to provide a way for the user
    to pass data to the workflow.

    Input nodes are always the first node in any policy or component.
    They are added by the engine, and should not be declared by the user.
    """

    def __init__(
        self, schema: dict[str, type], name="input_node", description: str | None = None
    ):
        super().__init__(
            name=name, typ=NodeType.INPUT, description=description, dependencies=None
        )
        self.schema = schema

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            metadata={
                "schema": {k: t.__name__ for k, t in self.schema.items()},
            },
        )


class Map(Node):
    """Produces a collection and splits it into elements.

    Map nodes are used as the entrypoint for Map-Transform-Collect patterns
    in the workflow. A `Map` node should produce a collection, which will
    be split into elements that can then be processed individually by
    a sub-workflow. At some point, the elements need to be collected back
    into a single collection, which is done by a `Collect` node.

    The simplest useful pattern is to use a `Map` node to make a list of
    things, apply a `Transform` node to each element, and `Collect` the results.
    This would look like:
    ```
                        -> a -> f(a) ->
                      /                 \
    map -> [a, b, c] -  -> b -> f(b) ->  -> collect -> [f(a), f(b), f(c)]
                      \                 /
                        -> c -> f(c) ->
    ```

    """

    def __init__(
        self,
        name: str,
        func: callable,
        dependencies: dict[str, Any],
        description: str | None = None,
        hidden: bool = False,
    ):
        """Produces a collection and splits it into elements.

        Parameters
        ----------
        name : str
            The name of the node.
        func: callable
            An arbitrary function that will be executed when the node is run.
            Should return a collection, which will be split into
            elements that can be processed individually.
        dependencies: dict, optional
            The dependencies of the node.
        description: str, optional
            A description of the node.
        hidden: bool, optional, default=False
            Whether the node should be hidden from the user interface.
            Mainly for internal use.

        """
        
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.MAP,
            dependencies=dependencies,
            hidden=hidden,
        )
        self.func = func

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            hidden=self.hidden,
            dependencies=self.node_dependencies(),
            metadata={
                "source": getsource(self.func),
            },
        )


class Collect(Node):
    """Collect dynamic outputs from a Map dynamic node or child nodes.

    Collect nodes are used to collect the outputs of a `Map` node or
    the outputs of its child nodes. They simply aggregate the results
    and produce a collection of outputs.

    See `Map` for more information.
    """

    def __init__(
        self,
        name: str,
        func: callable,
        dependencies: dict[str, Dependency],
        description: str | None = None,
        hidden: bool = False,
    ):
        """Collect dynamic outputs from a Map dynamic node."""
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.COLLECT,
            dependencies=dependencies,
            hidden=hidden,
        )
        self.func = func

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            hidden=self.hidden,
            dependencies=self.node_dependencies(),
            metadata={
                "source": getsource(self.func),
            },
        )
