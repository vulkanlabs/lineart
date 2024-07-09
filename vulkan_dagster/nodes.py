from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import requests
from dagster import Config, DependencyDefinition, In, OpDefinition, Out, Output


class NodeType(Enum):
    TRANSFORM = 1
    CONNECTION = 2
    BRANCH = 3
    INPUT = 4


class Status(Enum):
    APPROVED = "Approved"
    DENIED = "Denied"
    ANALYSIS = "Analysis"


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

    def __init__(
        self,
        config: HTTPConnectionConfig,
        params: Optional[dict] = None,
        dependencies: Optional[dict] = None,
    ):
        super().__init__(config)
        self.params = params if params is not None else {}
        self.dependencies = dependencies if dependencies is not None else {}

    def node(self):
        node_op = OpDefinition(
            compute_fn=self.run,
            name=self.config.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={"result": Out()},
        )
        deps = _generate_dependencies(self.dependencies)
        return node_op, deps

    def run(self, context, inputs):
        context.log.debug(f"Requesting {self.config.url}")
        body = inputs.get("body", None)
        context.log.debug(f"Body: {body}")
        response = requests.request(
            method=self.config.method,
            url=self.config.url,
            headers=self.config.headers,
            params=self.params,
            data=body,
        )

        if response.status_code == 200:
            yield Output(response.json())
        else:
            context.log.error(
                f"Failed op {self.config.name} with status {response.status_code}"
            )
            raise Exception("Connection failed")


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


class MultiBranch(Node):
    def __init__(
        self,
        config: NodeConfig,
        func: callable,
        params: dict[str, Any],
        outputs: list[str, str],
    ):
        super().__init__(config)
        self.func = func
        self.params = params
        self.outputs = outputs

    def node(self):
        # Wrap self.func to provide the expected bhv
        def fn(context, inputs):
            output = self.func(context, **inputs)
            yield Output(None, output)

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.config.name,
            ins={k: In() for k in self.params.keys()},
            outs={out: Out(is_required=False) for out in self.outputs},
        )
        deps = _generate_dependencies(self.params)
        return node_op, deps


class Input(Node):
    def __init__(self, config: NodeConfig, config_schema: dict):
        super().__init__(config)
        self.config_schema = config_schema

    def node(self):
        node_op = OpDefinition(
            compute_fn=self.run,
            name=self.config.name,
            ins={},
            outs={"result": Out()},
            config_schema=self.config_schema,
        )
        return node_op, None

    def run(self, context, *args, **kwargs):
        config = context.op_config
        context.log.info(f"Got Config: {config}")
        # Dict with config data
        yield Output(config)


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
    return deps
