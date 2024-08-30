from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from inspect import getsource
from typing import Any

from vulkan.core.dependency import Dependency


class NodeType(Enum):
    TRANSFORM = "TRANSFORM"
    TERMINATE = "TERMINATE"
    CONNECTION = "CONNECTION"
    COMPONENT = "COMPONENT"
    BRANCH = "BRANCH"
    INPUT = "INPUT"


@dataclass
class VulkanNodeDefinition:
    name: str
    description: str
    node_type: str
    hidden: bool = False
    dependencies: dict[str, Dependency] | None = None
    metadata: dict[str, Any] | None = None


class Node(ABC):
    def __init__(
        self,
        name: str,
        description: str,
        typ: NodeType,
        hidden: bool = False,
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
        description: str,
        url: str,
        method: str,
        headers: dict,
        params: dict | None = None,
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
        description: str,
        func: callable,
        dependencies: dict[str, Any],
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
        description: str,
        return_status: str,
        dependencies: dict[str, Any],
    ):
        self.return_status = return_status
        assert dependencies is not None, f"Dependencies not set for TERMINATE op {name}"
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.TERMINATE,
            dependencies=dependencies,
        )

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
        description: str,
        func: callable,
        outputs: list[str],
        dependencies: dict[str, Any],
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
    def __init__(self, description: str, schema: dict[str, type], name="input_node"):
        super().__init__(
            name=name, description=description, typ=NodeType.INPUT, dependencies=None
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


ConstuctorFromType = {
    NodeType.TRANSFORM: TransformNode,
    NodeType.TERMINATE: TerminateNode,
    NodeType.CONNECTION: HTTPConnectionNode,
    NodeType.BRANCH: BranchNode,
    NodeType.INPUT: InputNode,
}


class NodeFactory:
    def __init__(
        self,
        type: NodeType,
        static_params: dict[str, Any],
        instance_params: dict[str, Any],
    ):
        self.type = type
        self.static_params = static_params
        self.instance_params = instance_params

    def create(self, **kwargs) -> Node:
        params = self.static_params.copy()

        for name, alias in self.instance_params.items():
            if alias not in kwargs.keys():
                raise ValueError(f"Missing value for instance parameter {name}")
            params[name] = kwargs[alias]

        return ConstuctorFromType[self.type](**params)
