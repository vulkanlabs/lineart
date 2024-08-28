import time
from abc import ABC, abstractmethod
from enum import Enum
from traceback import format_exception_only
from typing import Any

import requests
from dagster import (
    In,
    OpDefinition,
    OpExecutionContext,
    Out,
    Output,
)

from ..core.exceptions import UserCodeException
from ..core.nodes import (
    BranchNode,
    HTTPConnectionNode,
    InputNode,
    TerminateNode,
    TransformNode,
)
from ..core.run import RunStatus
from ..core.step_metadata import StepMetadata
from .io_manager import METADATA_OUTPUT_KEY, PUBLISH_IO_MANAGER_KEY
from .run_config import RUN_CONFIG_KEY


# TODO: we should review how to require users to define the possible return
# values for each policy and then ensure that the values adhere to it.
class UserStatus(Enum):
    pass


class DagsterNode(ABC):

    @abstractmethod
    def op(self) -> OpDefinition:
        """Construct the Dagster op for this node."""


class HTTPConnection(HTTPConnectionNode, DagsterNode):

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
            url=url,
            method=method,
            headers=headers,
            params=params,
            dependencies=dependencies,
        )

    def op(self) -> OpDefinition:
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
            yield Output(response.content)
        else:
            context.log.error(
                f"Failed op {self.name} with status {response.status_code}"
            )
            raise Exception("Connection failed")


class TransformNodeMixin(DagsterNode):

    def op(self) -> OpDefinition:
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


class Transform(TransformNode, TransformNodeMixin):

    def __init__(
        self,
        name: str,
        description: str,
        func: callable,
        dependencies: dict[str, Any],
        hidden: bool = False,
    ):
        super().__init__(name, description, func, dependencies, hidden)
        self.func = func


class Terminate(TerminateNode, TransformNodeMixin):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: UserStatus,
        dependencies: dict[str, Any],
    ):
        super().__init__(name, description, return_status, dependencies)
        self.func = self._fn

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
            run_id=vulkan_run_config.run_id,
            status=self.return_status,
            **kwargs,
        )
        if not reported:
            raise ValueError("Callback function failed")
        return self.return_status

    def _terminate(
        self,
        context: OpExecutionContext,
        result: UserStatus,
    ) -> bool:
        vulkan_run_config = getattr(context.resources, RUN_CONFIG_KEY)
        server_url = vulkan_run_config.server_url
        run_id = vulkan_run_config.run_id

        url = f"{server_url}/runs/{run_id}"
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


class Branch(BranchNode, DagsterNode):
    def __init__(
        self,
        name: str,
        description: str,
        func: callable,
        outputs: list[str],
        dependencies: dict[str, Any],
    ):
        super().__init__(name, description, func, outputs, dependencies)

    def op(self) -> OpDefinition:
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


class Input(InputNode, DagsterNode):
    def __init__(self, description: str, schema: dict[str, type], name="input_node"):
        super().__init__(name=name, description=description, schema=schema)

    def run(self, context, *args, **kwargs):
        config = context.op_config
        context.log.info(f"Got Config: {config}")
        yield Output(config)

    def op(self):
        return OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={},
            outs={"result": Out()},
            config_schema=self.schema,
        )
