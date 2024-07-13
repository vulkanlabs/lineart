from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

import requests
from dagster import DependencyDefinition, In, OpDefinition, Out, Output


class NodeType(Enum):
    TRANSFORM = 1
    CONNECTION = 2
    BRANCH = 3
    INPUT = 4


class Status(Enum):
    APPROVED = "Approved"
    DENIED = "Denied"
    ANALYSIS = "Analysis"


class Node(ABC):

    def __init__(self, name, description, typ):
        self.name = name
        self.description = description
        self.type = typ

    @abstractmethod
    def node(self):
        pass


class HTTPConnection(Node):

    def __init__(
        self,
        name: str,
        description: str,
        url: str,
        method: str,
        headers: dict,
        params: Optional[dict] = None,
        dependencies: Optional[dict] = None,
    ):
        super().__init__(name, description, NodeType.CONNECTION)
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params if params is not None else {}
        self.dependencies = dependencies if dependencies is not None else {}

    def node(self):
        node_op = OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={"result": Out()},
        )
        deps = _generate_dependencies(self.dependencies)
        return node_op, deps

    def run(self, context, inputs):
        context.log.debug(f"Requesting {self.url}")
        body = inputs.get("body", None)
        context.log.debug(f"Body: {body}")
        response = requests.request(
            method=self.method,
            url=self.url,
            headers=self.headers,
            params=self.params,
            data=body,
        )

        if response.status_code == 200:
            yield Output(response.json())
        else:
            context.log.error(
                f"Failed op {self.name} with status {response.status_code}"
            )
            raise Exception("Connection failed")


class Transform(Node):

    def __init__(
        self,
        name: str,
        description: str,
        func: callable,
        params: dict[str, Any],
    ):
        super().__init__(name, description, NodeType.TRANSFORM)
        self.func = func
        self.params = params

    def node(self):
        # Wrap self.func to provide the expected bhv
        def fn(context, inputs):
            yield Output(self.func(context, **inputs))

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.params.keys()},
            outs={"result": Out()},
        )
        deps = _generate_dependencies(self.params)

        return node_op, deps


class Terminate(Transform):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: Status,
        dependencies: dict[str, Any],
    ):
        self.return_status = return_status
        self._fn = lambda _, **kwargs: self.return_status
        super().__init__(name, description, self._fn, dependencies)


class Branch(Node):
    def __init__(
        self,
        name: str,
        description: str,
        func: callable,
        params: dict[str, Any],
        outputs: list[str, str],
    ):
        super().__init__(name, description, NodeType.BRANCH)
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
            name=self.name,
            ins={k: In() for k in self.params.keys()},
            outs={out: Out(is_required=False) for out in self.outputs},
        )
        deps = _generate_dependencies(self.params)
        return node_op, deps


class Input(Node):
    def __init__(self, name: str, description: str, config_schema: dict):
        super().__init__(name, description, NodeType.INPUT)
        self.config_schema = config_schema

    def node(self):
        node_op = OpDefinition(
            compute_fn=self.run,
            name=self.name,
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
