from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from inspect import getsource
from typing import Any, Callable

from vulkan.core.dependency import Dependency


class NodeType(Enum):
    TRANSFORM = "TRANSFORM"
    TERMINATE = "TERMINATE"
    CONNECTION = "CONNECTION"
    COMPONENT = "COMPONENT"
    BRANCH = "BRANCH"
    INPUT = "INPUT"
    MAP = "MAP"
    COLLECT = "COLLECT"


@dataclass
class VulkanNodeDefinition:
    name: str
    node_type: str
    hidden: bool = False
    description: str | None = None
    dependencies: dict[str, Dependency] | None = None
    metadata: dict[str, Any] | None = None


class Node(ABC):
    def __init__(
        self,
        name: str,
        typ: NodeType,
        hidden: bool = False,
        description: str | None = None,
        dependencies: dict[str, Dependency] | None = None,
    ):
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


class TransformNode(Node):
    def __init__(
        self,
        name: str,
        func: callable,
        dependencies: dict[str, Any],
        description: str | None = None,
        hidden: bool = False,
    ):
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
    def __init__(
        self,
        name: str,
        return_status: str,
        dependencies: dict[str, Any],
        description: str | None = None,
        callback: Callable | None = None,
    ):
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
    def __init__(
        self,
        name: str,
        func: callable,
        outputs: list[str],
        dependencies: dict[str, Any],
        description: str | None = None,
    ):
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
    def __init__(
        self,
        name: str,
        func: callable,
        dependencies: dict[str, Any],
        description: str | None = None,
        hidden: bool = False,
    ):
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