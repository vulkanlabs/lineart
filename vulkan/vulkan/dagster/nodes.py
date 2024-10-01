import time
from abc import ABC, abstractmethod
from enum import Enum
from traceback import format_exception_only
from typing import Any, Callable, Iterable

import requests
from dagster import (
    DynamicOut,
    DynamicOutput,
    In,
    OpDefinition,
    OpExecutionContext,
    Out,
    Output,
)

from vulkan.core.run import RunStatus
from vulkan.core.step_metadata import StepMetadata
from vulkan.dagster.io_manager import METADATA_OUTPUT_KEY, PUBLISH_IO_MANAGER_KEY
from vulkan.dagster.run_config import RUN_CONFIG_KEY
from vulkan.exceptions import UserCodeException
from vulkan.spec.nodes import (
    BranchNode,
    Collect,
    HTTPConnectionNode,
    InputNode,
    Map,
    Node,
    TerminateNode,
    TransformNode,
)


# TODO: we should review how to require users to define the possible return
# values for each policy and then ensure that the values adhere to it.
class UserStatus(Enum):
    pass


class DagsterNode(ABC):
    @abstractmethod
    def op(self) -> OpDefinition:
        """Construct the Dagster op for this node."""


class DagsterHTTPConnection(HTTPConnectionNode, DagsterNode):
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
            outs={
                "result": Out(),
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
            },
        )

    def run(self, context, inputs):
        start_time = time.time()
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

        error = None
        try:
            response.raise_for_status()
            if response.status_code == 200:
                yield Output(response.content)
        except requests.exceptions.RequestException as e:
            context.log.error(
                f"Failed op {self.name} with status {response.status_code}"
            )
            error = ("\n").join(format_exception_only(type(e), e))
            raise e
        finally:
            end_time = time.time()
            metadata = StepMetadata(
                node_type=self.type.value,
                start_time=start_time,
                end_time=end_time,
                error=error,
                extra={
                    "status_code": response.status_code,
                    "url": self.url,
                    "method": self.method,
                },
            )
            yield Output(metadata, output_name=METADATA_OUTPUT_KEY)

    @classmethod
    def from_spec(cls, node: HTTPConnectionNode):
        return cls(
            name=node.name,
            description=node.description,
            url=node.url,
            method=node.method,
            headers=node.headers,
            params=node.params,
            dependencies=node.dependencies,
        )


class DagsterTransformNodeMixin(DagsterNode):
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


class DagsterTransform(TransformNode, DagsterTransformNodeMixin):
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
            func=func,
            dependencies=dependencies,
            hidden=hidden,
        )

    @classmethod
    def from_spec(cls, node: TransformNode):
        return cls(
            name=node.name,
            description=node.description,
            func=node.func,
            dependencies=node.dependencies,
            hidden=node.hidden,
        )


class DagsterTerminate(TerminateNode, DagsterTransformNodeMixin):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: UserStatus,
        dependencies: dict[str, Any],
        callback: Callable | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            return_status=return_status,
            dependencies=dependencies,
            callback=callback,
        )
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
            return_status=self.return_status,
            **kwargs,
        )
        if not reported:
            raise ValueError("Callback function failed")
        return self.return_status.value

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

    @classmethod
    def from_spec(cls, node: TerminateNode):
        return cls(
            name=node.name,
            description=node.description,
            return_status=node.return_status,
            dependencies=node.dependencies,
            callback=node.callback,
        )


class DagsterBranch(BranchNode, DagsterNode):
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
            func=func,
            outputs=outputs,
            dependencies=dependencies,
        )

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
                    extra={"choices": self.outputs},
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

    @classmethod
    def from_spec(cls, node: BranchNode):
        return cls(
            name=node.name,
            description=node.description,
            func=node.func,
            outputs=node.outputs,
            dependencies=node.dependencies,
        )


class DagsterInput(InputNode, DagsterNode):
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

    @classmethod
    def from_spec(cls, node: InputNode):
        return cls(
            name=node.name,
            description=node.description,
            schema=node.schema,
        )


class DagsterMap(Map, DagsterNode):
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
            func=func,
            dependencies=dependencies,
            hidden=hidden,
        )

    def op(self) -> OpDefinition:
        def fn(context, inputs):
            start_time = time.time()
            error = None
            try:
                result = self.func(context, **inputs)
                assert isinstance(
                    result, Iterable
                ), f"DynamicTransform functions must return an iterable, got: {result}"
                context.log.info(f"Returning {len(result)} outputs")
                for i, e in enumerate(result):
                    yield DynamicOutput(
                        e,
                        mapping_key=str(i),
                        output_name="result",
                    )
            except Exception as e:
                error = ("\n").join(format_exception_only(type(e), e))
                raise UserCodeException(self.name) from e
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
                "result": DynamicOut(),
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
            },
            # We expose the configuration in transform nodes
            # to allow the callback function in terminate nodes to
            # access it. In the future, we may separate terminate nodes.
            required_resource_keys={RUN_CONFIG_KEY},
        )

        return node_op

    @classmethod
    def from_spec(cls, node: Map):
        return cls(
            name=node.name,
            description=node.description,
            func=node.func,
            dependencies=node.dependencies,
            hidden=node.hidden,
        )


class DagsterCollect(Collect, DagsterTransformNodeMixin):
    def __init__(
        self,
        name: str,
        func: callable,
        description: str,
        dependencies: dict[str, Any],
        hidden: bool = False,
    ):
        super().__init__(
            name=name,
            description=description,
            func=func,
            dependencies=dependencies,
            hidden=hidden,
        )

    @classmethod
    def from_spec(cls, node: Collect):
        return cls(
            name=node.name,
            description=node.description,
            func=node.func,
            dependencies=node.dependencies,
            hidden=node.hidden,
        )


_NODE_TYPE_MAP: dict[type[Node], type[DagsterNode]] = {
    TransformNode: DagsterTransform,
    TerminateNode: DagsterTerminate,
    BranchNode: DagsterBranch,
    HTTPConnectionNode: DagsterHTTPConnection,
    InputNode: DagsterInput,
    Collect: DagsterCollect,
    Map: DagsterMap,
}


def to_dagster_nodes(nodes: list[Node]) -> list[DagsterNode]:
    return [to_dagster_node(node) for node in nodes]


def to_dagster_node(node: Node) -> DagsterNode:
    typ = type(node)
    impl_type = _NODE_TYPE_MAP.get(typ)
    if impl_type is None:
        msg = f"Node type {typ} has no known Dagster implementation"
        raise ValueError(msg)

    return impl_type.from_spec(node)
