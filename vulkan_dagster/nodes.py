from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional

import requests
from dagster import (
    DependencyDefinition,
    GraphDefinition,
    In,
    OpDefinition,
    OpExecutionContext,
    Out,
    Output,
)


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
    def node(self) -> OpDefinition:
        pass

    @abstractmethod
    def graph_dependencies(self) -> dict[str, Any]:
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

    def node(self) -> OpDefinition:
        return OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={"result": Out()},
        )

    def graph_dependencies(self) -> dict[str, Any]:
        return _generate_dependencies(self.dependencies)

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

    def node(self) -> OpDefinition:
        def fn(context, inputs):
            yield Output(self.func(context, **inputs))

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.params.keys()},
            outs={"result": Out()},
        )

        return node_op

    def graph_dependencies(self) -> dict[str, Any]:
        return _generate_dependencies(self.params)


class Terminate(Transform):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: Status,
        dependencies: dict[str, Any],
    ):
        self.return_status = return_status
        _internal_dependencies = {
            "run_id": "_run_id",
            "policy_id": "_policy_id",
            "server_url": "_server_url",
        }
        all_dependencies = {**dependencies, **_internal_dependencies}
        super().__init__(name, description, self._fn, all_dependencies)

    def _fn(self, context, policy_id, run_id, server_url, **kwargs):
        context.log.info(f"Terminating with status {self.return_status}")
        if self.callback is None:
            raise ValueError(f"Callback function not set for op {self.name}")

        self._terminate(context, server_url, policy_id, run_id, self.return_status)

        context.log.debug("Executing callback function")
        reported = self.callback(
            context=context,
            policy_id=policy_id,
            run_id=run_id,
            status=self.return_status,
        )
        if not reported:
            raise ValueError("Callback function failed")
        return self.return_status

    def _terminate(
        self,
        context: OpExecutionContext,
        server_url: str,
        policy_id: int,
        run_id: int,
        status: Status,
    ) -> bool:
        url = f"{server_url}/policies/{policy_id}/runs/{run_id}"
        dagster_run_id: str = context.run_id
        status: str = status.value
        context.log.info(f"Returned status {status} to {url} for run {dagster_run_id}")
        result = requests.put(
            url, data={"dagster_run_id": dagster_run_id, "status": status}
        )
        if result.status_code not in {200, 204}:
            msg = f"Error {result.status_code} Failed to return status {status} to {url} for run {dagster_run_id}"
            context.log.error(msg)
            return False
        return True

    def with_callback(self, callback: callable) -> "Terminate":
        self.callback = callback
        return self


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

    def node(self) -> OpDefinition:
        def fn(context, inputs):
            output = self.func(context, **inputs)
            yield Output(None, output)

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.params.keys()},
            outs={out: Out(is_required=False) for out in self.outputs},
        )
        return node_op

    def graph_dependencies(self) -> dict[str, Any]:
        return _generate_dependencies(self.params)


class Input(Node):
    def __init__(self, name: str, description: str, config_schema: dict):
        super().__init__(name, description, NodeType.INPUT)
        self.config_schema = config_schema

    def run(self, context, *args, **kwargs):
        config = context.op_config
        context.log.info(f"Got Config: {config}")
        yield Output(config)

    def node(self):
        return OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={},
            outs={"result": Out()},
            config_schema=self.config_schema,
        )

    def graph_dependencies(self) -> dict[str, Any]:
        return None


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


class Policy:
    def __init__(
        self,
        name: str,
        description: str,
        nodes: list[Node],
        input_schema: dict[str, type],
        output_callback: callable,
    ):
        assert len(nodes) > 0, "Policy must have at least one node"
        assert all(
            isinstance(n, Node) for n in nodes
        ), "All elements must be of type Node"
        assert all(
            isinstance(k, str) and isinstance(v, type) for k, v in input_schema.items()
        ), "Input schema must be a dictionary of str -> type"

        self.name = name
        self.description = description
        internal_input_schema = {
            "policy_id": int,
            "run_id": int,
            "server_url": str,
        }
        self.input_schema = {**internal_input_schema, **input_schema}
        self.output_callback = output_callback

        internal_nodes = self._internal_nodes()
        self.nodes = self._update_nodes(nodes, internal_nodes)

    def graph(self):
        nodes = self._dagster_nodes()
        deps = self._graph_dependencies()

        return GraphDefinition(
            name=self.name,
            description=self.description,
            node_defs=nodes,
            dependencies=deps,
        )

    def _dagster_nodes(self):
        return [n.node() for n in self.nodes]

    def _graph_dependencies(self):
        return {
            n.name: n.graph_dependencies()
            for n in self.nodes
            if n.graph_dependencies() is not None
        }

    def to_job(self):
        return self.graph().to_job(self.name + "_job")

    def _internal_nodes(self) -> list[Node]:
        return [
            self._input_node(),
            self._run_id_node(),
            self._policy_id_node(),
            self._server_url_node(),
        ]

    def _input_node(self) -> Input:
        return Input(
            name="input_node",
            description="Input node",
            config_schema=self.input_schema,
        )

    def _run_id_node(self) -> Transform:
        return Transform(
            name="_run_id",
            description="Get the run id",
            func=lambda context, inputs, **kwargs: inputs["run_id"],
            params={"inputs": "input_node"},
        )

    def _policy_id_node(self) -> Transform:
        return Transform(
            name="_policy_id",
            description="Get the policy id",
            func=lambda context, inputs, **kwargs: inputs["policy_id"],
            params={"inputs": "input_node"},
        )

    def _server_url_node(self) -> Transform:
        return Transform(
            name="_server_url",
            description="Get the server url",
            func=lambda context, inputs, **kwargs: inputs["server_url"],
            params={"inputs": "input_node"},
        )

    def _update_nodes(self, nodes, internal_nodes):
        all_nodes = [*internal_nodes]
        for node in nodes:
            if isinstance(node, Terminate):
                node = node.with_callback(self.output_callback)
            all_nodes.append(node)

        return all_nodes


# TODO: add failure op hook to update run status in app.
