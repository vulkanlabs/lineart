import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from traceback import format_exception_only
from typing import Any, Optional

import requests
from dagster import (
    DependencyDefinition,
    In,
    OpDefinition,
    OpExecutionContext,
    Out,
    Output,
)

from .exceptions import UserCodeException
from .run import RUN_CONFIG_KEY, RunStatus
from .step_metadata import METADATA_OUTPUT_KEY, PUBLISH_IO_MANAGER_KEY, StepMetadata


class NodeType(Enum):
    TRANSFORM = "TRANSFORM"
    CONNECTION = "CONNECTION"
    BRANCH = "BRANCH"
    INPUT = "INPUT"


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

    def __init__(
        self,
        name: str,
        description: str,
        typ: NodeType,
        dependencies: dict | None = None,
    ):
        self.name = name
        self.description = description
        self.type = typ
        self.dependencies = dependencies if dependencies is not None else {}

    @abstractmethod
    def node(self) -> OpDefinition:
        pass

    def graph_dependencies(self) -> dict[str, Any]:
        if self.dependencies is None:
            return None

        deps = {}
        for k, v in self.dependencies.items():
            if isinstance(v, tuple):
                definition = DependencyDefinition(v[0], v[1])
            elif isinstance(v, str):
                definition = DependencyDefinition(v, "result")
            else:
                raise ValueError(f"Invalid dependency definition: {k} -> {v}")
            deps[k] = definition
        return deps


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
        super().__init__(name, description, NodeType.CONNECTION, dependencies)
        self.url = url
        self.method = method
        self.headers = headers
        self.params = params if params is not None else {}

    def node(self) -> OpDefinition:
        return OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={"result": Out()},
        )

    def run(self, context, inputs):
        context.log.debug(f"Requesting {self.url}")
        body = inputs.get("body", None)
        context.log.debug(f"Body: {body}")

        if self.headers.get("Content-Type") == "application/json":
            json = body
            data = None
        else:
            json = None
            data = body

        # TODO: review how we can customize request creation
        req = requests.Request(
            method=self.method,
            url=self.url,
            headers=self.headers,
            params=self.params,
            data=data,
            json=json,
        ).prepare()
        context.log.debug(
            f"Request: body {req.body}\n headers {req.headers} \n url {req.url}"
        )

        response = requests.Session().send(req)
        context.log.debug(f"Response: {response}")

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
        super().__init__(name, description, NodeType.TRANSFORM, dependencies)
        self.func = func

    def node(self) -> OpDefinition:
        def fn(context, inputs):
            start_time = time.time()
            error = None
            try:
                result = self.func(context, **inputs)
            except Exception as e:
                error = ("\n").join(format_exception_only(type(e), e))
                raise UserCodeException(self.name) from e
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


class Terminate(Transform):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: Status,
        dependencies: dict[str, Any],
    ):
        self.return_status = return_status
        assert dependencies is not None, f"Dependencies not set for TERMINATE op {name}"
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
        response = requests.put(
            url,
            json={
                "result": result,
                "status": RunStatus.SUCCESS.value,
            },
        )
        if response.status_code not in {200, 204}:
            msg = f"Error {response.status_code} Failed to return status {result} to {url} for run {dagster_run_id}"
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
        outputs: list[str],
    ):
        super().__init__(name, description, NodeType.BRANCH, dependencies)
        self.func = func
        self.outputs = outputs

    def node(self) -> OpDefinition:
        def fn(context, inputs):
            start_time = time.time()
            error = None
            try:
                output = self.func(context, **inputs)
            except Exception as e:
                error = format_exception_only(type(e), e)
                raise UserCodeException(self.name) from e
            else:
                yield Output(None, output)
            finally:
                end_time = time.time()
                metadata = StepMetadata(
                    self.type.value,
                    start_time,
                    end_time,
                    error,
                    {"choices": self.outputs},
                )
                yield Output(metadata, output_name=METADATA_OUTPUT_KEY)

        branch_paths = {out: Out(is_required=False) for out in self.outputs}
        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
                **branch_paths,
            },
        )
        return node_op


class Input(Node):
    def __init__(self, description: str, config_schema: dict, name="input_node"):
        super().__init__(name, description, NodeType.INPUT, dependencies=None)
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
