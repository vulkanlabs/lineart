import time
from abc import ABC, abstractmethod
from enum import Enum
from traceback import format_exception_only
from typing import Any, Callable

import requests
from dagster import In, OpDefinition, OpExecutionContext, Out, Output
from vulkan_public.constants import POLICY_CONFIG_KEY
from vulkan_public.core.context import VulkanExecutionContext
from vulkan_public.exceptions import UserCodeException
from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes import (
    BranchNode,
    DataInputNode,
    InputNode,
    Node,
    TerminateNode,
    TransformNode,
)

from vulkan.core.run import RunStatus
from vulkan.core.step_metadata import StepMetadata
from vulkan.dagster.io_manager import METADATA_OUTPUT_KEY, PUBLISH_IO_MANAGER_KEY
from vulkan.dagster.resources import DATA_CLIENT_KEY, VulkanDataClient
from vulkan.dagster.run_config import (
    RUN_CONFIG_KEY,
    VulkanPolicyConfig,
    VulkanRunConfig,
)


# TODO: we should review how to require users to define the possible return
# values for each policy and then ensure that the values adhere to it.
class UserStatus(Enum):
    pass


class DagsterNode(ABC):
    @abstractmethod
    def op(self) -> OpDefinition:
        """Construct the Dagster op for this node."""


class DagsterDataInput(DataInputNode, DagsterNode):
    def __init__(
        self,
        name: str,
        data_source: str,
        description: str | None = None,
        dependencies: dict | None = None,
    ):
        super().__init__(
            name=name,
            data_source=data_source,
            description=description,
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
            required_resource_keys={DATA_CLIENT_KEY, POLICY_CONFIG_KEY, RUN_CONFIG_KEY},
        )

    def run(self, context, inputs):
        start_time = time.time()
        client: VulkanDataClient = getattr(context.resources, DATA_CLIENT_KEY)
        env: VulkanPolicyConfig = getattr(context.resources, POLICY_CONFIG_KEY)
        run_config: VulkanRunConfig = getattr(context.resources, RUN_CONFIG_KEY)

        body = inputs.get("body", None)
        context.log.debug(f"Body: {body}")

        response = client.get_data(
            data_source=self.data_source,
            body=body,
            variables=env.variables,
            run_id=run_config.run_id,
        )
        context.log.debug(f"Response: {response}")

        error = None
        extra = dict(data_source=self.data_source, status_code=response.status_code)

        try:
            response.raise_for_status()
            if response.status_code == 200:
                data = response.json()
                response_metadata = {
                    "data_object_id": data.get("data_object_id"),
                    "request_key": data.get("key"),
                    "origin": data.get("origin"),
                }
                extra.update({"response_metadata": response_metadata})
                yield Output(data["value"])
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
                extra=extra,
            )
            yield Output(metadata, output_name=METADATA_OUTPUT_KEY)

    @classmethod
    def from_spec(cls, node: DataInputNode):
        return cls(
            name=_format_dagster_name(node.name),
            data_source=node.data_source,
            description=node.description,
            dependencies=_format_dagster_dependencies(node.dependencies),
        )


class DagsterTransformNodeMixin(DagsterNode):
    def op(self) -> OpDefinition:
        def fn(context, inputs):
            start_time = time.time()
            error = None
            try:
                result = self._func(context, **inputs)
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
            required_resource_keys={RUN_CONFIG_KEY, POLICY_CONFIG_KEY},
        )

        return node_op


def _with_vulkan_context(func: callable) -> callable:
    def fn(context: OpExecutionContext, **kwargs):
        if func.__code__.co_varnames[0] == "context":
            env = getattr(context.resources, POLICY_CONFIG_KEY)
            ctx = VulkanExecutionContext(logger=context.log, env=env.variables)
            return func(ctx, **kwargs)
        return func(**kwargs)

    return fn


class DagsterTransform(TransformNode, DagsterTransformNodeMixin):
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        dependencies: dict[str, Any],
    ):
        super().__init__(
            name=name,
            description=description,
            func=func,
            dependencies=dependencies,
        )
        self._func = _with_vulkan_context(self.func)

    @classmethod
    def from_spec(cls, node: TransformNode):
        return cls(
            name=_format_dagster_name(node.name),
            description=node.description,
            func=node.func,
            dependencies=_format_dagster_dependencies(node.dependencies),
        )


class DagsterTerminate(TerminateNode, DagsterTransformNodeMixin):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: UserStatus | str,
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
        self._func = self._fn

    def _fn(self, context, **kwargs):
        status = self.return_status
        result = status.value if isinstance(status, Enum) else status
        vulkan_run_config = context.resources.vulkan_run_config
        context.log.info(f"Terminating with status {status}")

        terminated = self._terminate(context, result)
        if not terminated:
            raise ValueError("Failed to terminate run")

        if self.callback is not None:
            reported = self.callback(
                context=context,
                run_id=vulkan_run_config.run_id,
                return_status=status,
                **kwargs,
            )
            if not reported:
                raise ValueError("Callback function failed")

        return result

    def _terminate(
        self,
        context: OpExecutionContext,
        result: str,
    ) -> bool:
        vulkan_run_config = getattr(context.resources, RUN_CONFIG_KEY)
        server_url = vulkan_run_config.server_url
        run_id = vulkan_run_config.run_id

        url = f"{server_url}/runs/{run_id}"
        dagster_run_id: str = context.run_id
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
            name=_format_dagster_name(node.name),
            description=node.description,
            return_status=node.return_status,
            dependencies=_format_dagster_dependencies(node.dependencies),
            callback=node.callback,
        )


class DagsterBranch(BranchNode, DagsterNode):
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        choices: list[str],
        dependencies: dict[str, Any],
    ):
        super().__init__(
            name=name,
            description=description,
            func=func,
            choices=choices,
            dependencies=dependencies,
        )
        self._func = _with_vulkan_context(self.func)

    def op(self) -> OpDefinition:
        def fn(context, inputs):
            start_time = time.time()
            error = None
            try:
                output = self._func(context, **inputs)
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
                    extra={"choices": self.choices},
                )
                yield Output(metadata, output_name=METADATA_OUTPUT_KEY)

        branch_paths = {out: Out(is_required=False) for out in self.choices}
        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
                **branch_paths,
            },
            required_resource_keys={POLICY_CONFIG_KEY},
        )
        return node_op

    @classmethod
    def from_spec(cls, node: BranchNode):
        return cls(
            name=_format_dagster_name(node.name),
            description=node.description,
            func=node.func,
            choices=node.choices,
            dependencies=_format_dagster_dependencies(node.dependencies),
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


_NODE_TYPE_MAP: dict[type[Node], type[DagsterNode]] = {
    TransformNode: DagsterTransform,
    TerminateNode: DagsterTerminate,
    BranchNode: DagsterBranch,
    DataInputNode: DagsterDataInput,
    InputNode: DagsterInput,
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


def _format_dagster_dependencies(
    dependencies: dict[str, Dependency],
) -> dict[str, Dependency]:
    return {k: _format_dagster_dependency(v) for k, v in dependencies.items()}


def _format_dagster_dependency(dependency: Dependency) -> Dependency:
    args = dependency.to_dict()
    args["node"] = _format_dagster_name(dependency.node)
    return Dependency.from_dict(args)


def _format_dagster_name(name: str) -> str:
    # Replace every character not in regex "^[A-Za-z0-9_]+$" with _
    return "".join(c if c.isalnum() or c == "_" else "_" for c in name)
