import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from inspect import getsource
from traceback import format_exception_only
from typing import Any, Optional

import requests
from dagster import (
    ConfigurableResource,
    DependencyDefinition,
    GraphDefinition,
    HookContext,
    In,
    OpDefinition,
    OpExecutionContext,
    Out,
    Output,
    failure_hook,
)

from .run import RUN_CONFIG_KEY, RunStatus
from .step_metadata import (
    METADATA_OUTPUT_KEY,
    PUBLISH_IO_MANAGER_KEY,
    StepMetadata,
)


class NodeType(Enum):
    TRANSFORM = 1
    CONNECTION = 2
    BRANCH = 3
    INPUT = 4


class Status(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ANALYSIS = "ANALYSIS"


@dataclass
class VulkanNodeDefinition:
    name: str
    description: str
    node_type: str
    dependencies: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


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
        dependencies: dict[str, Any],
    ):
        super().__init__(name, description, NodeType.TRANSFORM)
        self.func = func
        self.dependencies = dependencies

    def node(self) -> OpDefinition:
        def fn(context, inputs):
            start_time = time.time()
            error = None
            try:
                result = self.func(context, **inputs)
            except Exception as e:
                error = format_exception_only(type(e), e)
                # TODO: raise UserCodeException() from e
                raise e
            else:
                yield Output(result, output_name="result")
            finally:
                end_time = time.time()
                metadata = StepMetadata(
                    self.type.value,
                    start_time,
                    end_time,
                    error,
                )
                yield Output(metadata, output_name=METADATA_OUTPUT_KEY)

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                "result": Out(),
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
            },
            # We expose the configuration in transform nodes
            # to allow the callback function in terminate nodes to
            # access it. In the future, we may separate terminate nodes.
            required_resource_keys={RUN_CONFIG_KEY},
        )

        return node_op

    def graph_dependencies(self) -> dict[str, Any]:
        return _generate_dependencies(self.dependencies)


class Terminate(Transform):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: Status,
        dependencies: dict[str, Any],
    ):
        self.return_status = return_status
        super().__init__(name, description, self._fn, dependencies)

    def _fn(self, context, **kwargs):
        vulkan_run_config = context.resources.vulkan_run_config
        context.log.info(f"Terminating with status {self.return_status}")
        if self.callback is None:
            raise ValueError(f"Callback function not set for op {self.name}")

        terminated = self._terminate(context, self.return_status)
        if not terminated:
            raise ValueError("Failed to terminate run")

        reported = self.callback(
            context=context,
            policy_id=vulkan_run_config.policy_id,
            run_id=vulkan_run_config.run_id,
            status=self.return_status,
        )
        if not reported:
            raise ValueError("Callback function failed")
        return self.return_status

    def _terminate(
        self,
        context: OpExecutionContext,
        result: Status,
    ) -> bool:
        vulkan_run_config = getattr(context.resources, RUN_CONFIG_KEY)
        server_url = vulkan_run_config.server_url
        policy_id = vulkan_run_config.policy_id
        run_id = vulkan_run_config.run_id

        url = f"{server_url}/policies/{policy_id}/runs/{run_id}"
        dagster_run_id: str = context.run_id
        result: str = result.value
        context.log.info(f"Returning status {result} to {url} for run {dagster_run_id}")
        result = requests.put(
            url,
            data={
                "dagster_run_id": dagster_run_id,
                "result": result,
                "status": RunStatus.SUCCESS.value,
            },
        )
        if result.status_code not in {200, 204}:
            msg = f"Error {result.status_code} Failed to return status {result} to {url} for run {dagster_run_id}"
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
        dependencies: dict[str, Any],
        outputs: list[str, str],
    ):
        super().__init__(name, description, NodeType.BRANCH)
        self.func = func
        self.dependencies = dependencies
        self.outputs = outputs

    def node(self) -> OpDefinition:
        def fn(context, inputs):
            output = self.func(context, **inputs)
            yield Output(None, output)

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={out: Out(is_required=False) for out in self.outputs},
        )
        return node_op

    def graph_dependencies(self) -> dict[str, Any]:
        return _generate_dependencies(self.dependencies)


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


def _generate_dependencies(dependencies: dict):
    deps = {}
    for k, v in dependencies.items():
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
        assert callable(output_callback), "Output callback must be a callable"

        self.name = name
        self.description = description
        self.input_schema = input_schema
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

    def node_definitions(self):
        definitions = {}
        for node in self.nodes:
            opt_args = {}
            dagster_deps = node.graph_dependencies()
            if node.graph_dependencies() is not None:
                opt_args["dependencies"] = [v.node for k, v in dagster_deps.items()]
            if node.type == NodeType.TRANSFORM or node.type == NodeType.BRANCH:
                opt_args["metadata"] = {"executable": getsource(node.func)}

            definitions[node.name] = VulkanNodeDefinition(
                name=node.name,
                description=node.description,
                node_type=node.type,
                **opt_args,
            )
        return definitions

    def _dagster_nodes(self):
        return [n.node() for n in self.nodes]

    def _graph_dependencies(self):
        return {
            n.name: n.graph_dependencies()
            for n in self.nodes
            if n.graph_dependencies() is not None
        }

    def to_job(self, resources: dict[str, ConfigurableResource]):
        return self.graph().to_job(
            self.name + "_job",
            resource_defs=resources,
            hooks={_notify_failure},
        )

    def _internal_nodes(self) -> list[Node]:
        return [
            self._input_node(),
        ]

    def _input_node(self) -> Input:
        return Input(
            name="input_node",
            description="Input node",
            config_schema=self.input_schema,
        )

    def _update_nodes(self, nodes, internal_nodes):
        all_nodes = [*internal_nodes]
        for node in nodes:
            if isinstance(node, Terminate):
                node = node.with_callback(self.output_callback)
            all_nodes.append(node)

        return all_nodes


@failure_hook(required_resource_keys={RUN_CONFIG_KEY})
def _notify_failure(context: HookContext) -> bool:
    vulkan_run_config = context.resources.vulkan_run_config
    server_url = vulkan_run_config.server_url
    policy_id = vulkan_run_config.policy_id
    run_id = vulkan_run_config.run_id

    context.log.info(f"Notifying failure for run {run_id} in policy {policy_id}")
    url = f"{server_url}/policies/{policy_id}/runs/{run_id}"
    dagster_run_id: str = context.run_id
    result = requests.put(
        url,
        data={
            "dagster_run_id": dagster_run_id,
            "result": "",
            "status": RunStatus.FAILURE.value,
        },
    )
    if result.status_code not in {200, 204}:
        msg = f"Error {result.status_code} Failed to notify failure to {url} for run {dagster_run_id}"
        context.log.error(msg)
