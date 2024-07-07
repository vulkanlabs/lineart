from dagster import Output, OpDefinition, DependencyDefinition, In, Out
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import requests


class NodeType(Enum):
    TRANSFORM = 1
    CONNECTION = 2
    BRANCH = 3


class Status(Enum):
    APPROVED = 1
    DENIED = 2


@dataclass
class Context:
    data: dict[str, Any]
    variables: dict[str, Any]


@dataclass
class NodeConfig:
    name: str
    description: str
    type: NodeType


@dataclass
class HTTPConnectionConfig(NodeConfig):
    url: str
    method: str
    headers: dict
    params: dict


class Node(ABC):

    def __init__(self, config: NodeConfig):
        self.config = config

    @abstractmethod
    def node(self):
        pass


class HTTPConnection(Node):

    def __init__(self, config: HTTPConnectionConfig, params: Optional[dict] = None):
        super().__init__(config)
        self.params = params if params is not None else {}

    def node(self):
        node_op = OpDefinition(
            compute_fn=self.run,
            name=self.config.name,
            ins={},
            outs={"result": Out()},
        )
        deps = _generate_dependencies(self.params)
        return node_op, deps

    def run(self, context, inputs):
        response = requests.request(
            method=self.config.method,
            url=self.config.url,
            headers=self.config.headers,
            params=self.config.params,
        )
        if response.status_code == 200:
            yield Output(response.json())
        # handle exception in controller
        # raise Exception("Connection failed")


class Transform(Node):

    def __init__(self, config: NodeConfig, func: callable, params: dict[str, Any]):
        super().__init__(config)
        self.func = func
        self.params = params

    def node(self):
        # Wrap self.func to provide the expected bhv
        def fn(context, inputs):
            yield Output(self.func(context, **inputs))

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.config.name,
            ins={k: In() for k in self.params.keys()},
            outs={"result": Out()},
        )
        deps = _generate_dependencies(self.params)

        return node_op, deps


class Branch(Node):
    def __init__(
        self,
        config: NodeConfig,
        func: callable,
        params: dict[str, Any],
        left: str,
        right: str,
    ):
        super().__init__(config)
        self.func = func
        self.params = params
        self.left = left
        self.right = right

    def node(self):
        # Wrap self.func to provide the expected bhv
        def fn(context, inputs):
            condition = self.func(context, **inputs)
            if condition:
                yield Output(True, self.right)
            else:
                yield Output(False, self.left)

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.config.name,
            ins={k: In() for k in self.params.keys()},
            outs={
                self.left: Out(is_required=False),
                self.right: Out(is_required=False),
            },
        )
        deps = _generate_dependencies(self.params)
        return node_op, deps


def _generate_dependencies(params: dict):
    deps = {}
    for k, v in params.items():
        if isinstance(v, tuple):
            definition = DependencyDefinition(v[0], v[1])
        elif isinstance(v, str):
            definition = DependencyDefinition(v, "result")
        else:
            raise ValueError(f"Invalid dependency definition: {k} -> {v}")
        deps[k] = definition
    return depss
