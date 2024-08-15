from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from inspect import getsource
from typing import Any, Optional


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
    dependencies: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class Node(ABC):

    def __init__(
        self,
        name: str,
        description: str,
        typ: NodeType,
        dependencies: dict | None = None,
    ):
        self._name = name
        self.description = description
        self.type = typ
        self._dependencies = dependencies if dependencies is not None else {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> dict[str, Any]:
        return self._dependencies

    @abstractmethod
    def node_definition(self) -> VulkanNodeDefinition:
        pass

    def node_dependencies(self) -> list[str]:
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
            name,
            description,
            NodeType.CONNECTION,
            dependencies,
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
    ):
        super().__init__(name, description, NodeType.TRANSFORM, dependencies)
        self.func = func

    def node_definition(self) -> VulkanNodeDefinition:
        return VulkanNodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
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
        super().__init__(name, description, NodeType.TERMINATE, dependencies)

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
        super().__init__(name, description, NodeType.BRANCH, dependencies)
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
        super().__init__(name, description, NodeType.INPUT, dependencies=None)
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
