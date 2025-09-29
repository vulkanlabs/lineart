import json
from abc import ABC, abstractmethod
from dataclasses import asdict
from enum import Enum
from typing import Any, Callable, Dict

import requests
from hatchet_sdk import Context
from hatchet_sdk.runnables.types import TWorkflowInput
from pydantic import BaseModel
from requests.exceptions import HTTPError

from vulkan.connections import (
    HTTPConfig,
    RetryPolicy,
    format_response_data,
    make_request,
)
from vulkan.core.context import VulkanExecutionContext
from vulkan.core.run import RunStatus
from vulkan.core.step_metadata import StepMetadata
from vulkan.exceptions import UserCodeException
from vulkan.node_config import normalize_to_template, resolve_template
from vulkan.runners.shared.app_client import BaseAppClient, create_app_client
from vulkan.runners.shared.constants import POLICY_CONFIG_KEY, RUN_CONFIG_KEY
from vulkan.runners.shared.run_config import VulkanRunConfig
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import (
    BranchNode,
    ConnectionNode,
    DataInputNode,
    DecisionNode,
    InputNode,
    Node,
    TerminateNode,
    TransformNode,
)
from vulkan.spec.nodes.metadata import DecisionCondition, DecisionType


def normalize_node_id(node_id: str) -> str:
    """Normalize node ID for Hatchet compatibility."""
    return node_id.replace("-", "_").replace(".", "_")


class TaskOutput(BaseModel):
    """Output of a task."""

    step_name: str
    step_type: str
    data: Any


class HatchetNode(ABC):
    """Base class for Hatchet node implementations."""

    @abstractmethod
    def task_fn(self) -> Callable[[TWorkflowInput, Context], Any]:
        """Return the task function for this node."""

    @property
    @abstractmethod
    def task_name(self) -> str:
        """Return the task name."""

    def _get_parent_outputs(self, context: Context) -> Dict[str, Any]:
        """Extract inputs from Hatchet context."""
        parent_outputs = {
            k: context.data.parents[v.id].get("data")
            for k, v in self.dependencies.items()
        }

        return parent_outputs


# FIXME (antonio): this is a hack to publish metadata.
#
# It adds ~100ms per node execution, as it requires a trip to the app.
# It also adds a bunch of pressure on the app server.
# A better solution would be to publish metadata at the end of the run,
# or to have a process collect and publish metadata asynchronously.
#
# This could maybe be achieved by using Hatchet events or modding
# the metadata publication endpoint to ack and return immediately, then
# process the metadata in the background.
#
# A third, sep issue is that the client needs to be initialized per node,
# adding some more complexity to each node. Ideally, we'd initialize
# the client once per run, and share it across nodes.
def publish_metadata(context: Context, step_name: str, metadata: StepMetadata) -> None:
    try:
        store = _metadata_store(context)
    except RuntimeError as e:
        msg = f"Failed to get metadata store: {e}"
        context.log(msg)
        raise RuntimeError(msg) from e

    try:
        store.publish_step_metadata(
            step_name=step_name,
            metadata=asdict(metadata),
        )
    except ValueError as e:
        msg = f"Failed to publish metadata: {e}"
        context.log(msg)
        raise RuntimeError(msg) from e


def _metadata_store(context: Context) -> BaseAppClient:
    """Return a metadata store client."""
    run_config = context.additional_metadata.get(RUN_CONFIG_KEY)
    if run_config is None:
        raise RuntimeError("Run configuration not found in context")

    return create_app_client(
        server_url=run_config.get("server_url"),
        run_id=run_config.get("run_id"),
        project_id=run_config.get("project_id"),
    )


class HatchetDataInput(DataInputNode, HatchetNode):
    """Hatchet implementation of DataInputNode."""

    def __init__(
        self,
        name: str,
        data_source: str,
        description: str | None = None,
        parameters: dict[str, str] | None = None,
        dependencies: dict | None = None,
    ):
        super().__init__(
            name=name,
            data_source=data_source,
            description=description,
            parameters=parameters,
            dependencies=dependencies,
        )

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], Any]:
        def data_input_task(
            workflow_input: TWorkflowInput, context: Context
        ) -> Dict[str, Any]:
            # Get resources from context (would need to be passed in)
            run_cfg = context.additional_metadata.get(RUN_CONFIG_KEY)

            if not run_cfg:
                raise RuntimeError("Required resources not available in context")

            run_config = VulkanRunConfig(**run_cfg)
            client: BaseAppClient = create_app_client(**run_cfg)

            inputs = self._get_parent_outputs(context)
            extra = dict(data_source=self.data_source)

            try:
                configured_params = self._get_configured_params(inputs)
            except ValueError as e:
                raise e

            try:
                response: requests.Response = client.fetch_data(
                    data_source=self.data_source,
                    configured_params=configured_params,
                )
                extra.update({"status_code": response.status_code})
                response.raise_for_status()
            except (requests.exceptions.RequestException, HTTPError) as e:
                raise e

            data = response.json()
            response_metadata = {
                "data_object_id": data.get("data_object_id"),
                "request_key": data.get("key"),
                "origin": data.get("origin"),
            }
            # TODO: log this somewhere useful
            extra.update({"response_metadata": response_metadata})
            return TaskOutput(
                step_name=self.name,
                step_type=self.type.value,
                data=data["value"],
            )

        return data_input_task

    def _get_configured_params(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Get configured parameters with template resolution."""
        if self.parameters is None:
            return {}

        configured_params = {}
        for k, v in self.parameters.items():
            try:
                configured_params[k] = resolve_template(v, inputs, env_variables={})
            except Exception:
                raise ValueError(f"Invalid parameter configuration: {v}")
        return configured_params

    @classmethod
    def from_spec(cls, node: DataInputNode):
        return cls(
            name=normalize_node_id(node.id),
            data_source=node.data_source,
            description=node.description,
            parameters=node.parameters,
            dependencies=node.dependencies,
        )


class HatchetTransform(TransformNode, HatchetNode):
    """Hatchet implementation of TransformNode."""

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        dependencies: dict[str, Any],
        parameters: dict[str, str] | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            func=func,
            dependencies=dependencies,
            parameters=parameters,
        )
        self._func = self._with_vulkan_context(self.func)

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], Any]:
        def transform_task(workflow_input: TWorkflowInput, context: Context) -> Any:
            inputs = self._get_parent_outputs(context)
            configured_params = self._get_configured_params(inputs)

            try:
                fn_params = {**inputs, **configured_params}
                result = self._func(context, **fn_params)
                return TaskOutput(
                    step_name=self.name,
                    step_type=self.type.value,
                    data=result,
                )
            except Exception as e:
                raise UserCodeException(self.name) from e

        return transform_task

    def _with_vulkan_context(self, func: Callable) -> Callable:
        """Wrap function with Vulkan context."""

        def fn(context: Context, **kwargs):
            if func.__code__.co_varnames[0] == "context":
                env = context.additional_metadata.get(POLICY_CONFIG_KEY)
                ctx = VulkanExecutionContext(
                    logger=context.logger if hasattr(context, "logger") else None,
                    env=env.variables if env else {},
                )
                return func(ctx, **kwargs)
            return func(**kwargs)

        return fn

    def _get_configured_params(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Get configured parameters with template resolution."""
        if self.parameters is None:
            return {}

        configured_params = {}
        for k, v in self.parameters.items():
            try:
                configured_params[k] = resolve_template(v, inputs, env_variables={})
            except Exception:
                raise ValueError(f"Invalid parameter configuration: {v}")
        return configured_params

    @classmethod
    def from_spec(cls, node: TransformNode):
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            func=node.func,
            dependencies=node.dependencies,
            parameters=node.parameters,
        )


class HatchetTerminate(TerminateNode, HatchetNode):
    """Hatchet implementation of TerminateNode."""

    def __init__(
        self,
        name: str,
        description: str,
        return_status: str,
        dependencies: dict[str, Dependency],
        output_data: dict[str, str] | None = None,
        callback: Callable | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            return_status=return_status,
            dependencies=dependencies,
            output_data=output_data,
            callback=callback,
        )

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], Any]:
        def terminate_task(workflow_input: TWorkflowInput, context: Context) -> str:
            inputs = self._get_parent_outputs(context)

            try:
                status = self.return_status
                result = status.value if isinstance(status, Enum) else status
                run_config = context.additional_metadata.get(RUN_CONFIG_KEY)

                metadata = None
                if self.return_metadata is not None:
                    try:
                        template_metadata = json.loads(self.return_metadata)
                        metadata = self._resolve_json_metadata(
                            template_metadata, inputs, context
                        )
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON in return_metadata: {e}")
                    except Exception as e:
                        raise ValueError(f"Failed to resolve JSON metadata: {e}")

                try:
                    self._terminate(context, result, metadata)
                except ValueError as e:
                    raise ValueError("Failed to terminate run") from e

                if self.callback is not None:
                    reported = self.callback(
                        context=context,
                        run_id=run_config.run_id if run_config else None,
                        return_status=status,
                        **inputs,
                    )
                    if not reported:
                        raise ValueError("Callback function failed")

                return TaskOutput(
                    step_name=self.name,
                    step_type=self.type.value,
                    data=result,
                )

            except Exception as e:
                raise e

        return terminate_task

    def _resolve_json_metadata(
        self, template_metadata: dict, inputs: dict, context: Context
    ) -> dict:
        """Resolve JSON metadata templates."""

        def resolve_value(value):
            if isinstance(value, str):
                try:
                    env_config = context.additional_metadata.get(POLICY_CONFIG_KEY)
                    env_variables = env_config.variables if env_config else {}
                    return resolve_template(value, inputs, env_variables)
                except Exception:
                    return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            else:
                return value

        return resolve_value(template_metadata)

    def _terminate(
        self, context: Context, result: str, metadata: Dict[str, Any] | None = None
    ) -> bool:
        """Terminate the run by notifying the server."""
        run_config_dict = context.additional_metadata.get(RUN_CONFIG_KEY)
        if not run_config_dict:
            raise ValueError(
                f"Run configuration not found in context: {context.additional_metadata}"
            )
        run_config = VulkanRunConfig(**run_config_dict)

        server_url = run_config.server_url
        run_id = run_config.run_id
        context.log(f"Terminating run {run_config.run_id} with result {result}")
        context.log(f"Posting to {server_url}")

        url = f"{server_url}/internal/runs/{run_id}"
        response = requests.put(
            url,
            json={
                "result": result,
                "metadata": metadata,
                "status": RunStatus.SUCCESS.value,
            },
        )
        if response.status_code not in {200, 204}:
            raise ValueError(
                f"Failed to terminate run {run_id}. Status code: {response.status_code}, Response: {response.text}"
            )

    @classmethod
    def from_spec(cls, node: TerminateNode):
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            return_status=node.return_status,
            output_data=node.output_data,
            dependencies=node.dependencies,
            callback=node.callback,
        )


class HatchetBranch(BranchNode, HatchetNode):
    """Hatchet implementation of BranchNode."""

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
        self._func = self._with_vulkan_context(self.func)

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], Any]:
        def branch_task(workflow_input: TWorkflowInput, context: Context) -> str:
            inputs = self._get_parent_outputs(context)

            try:
                context.log(f"Branching on {self.name} with inputs {inputs}")
                output = self._func(context, **inputs)
                return TaskOutput(
                    step_name=self.name,
                    step_type=self.type.value,
                    data=output,
                )
            except Exception as e:
                raise UserCodeException(self.name) from e

        return branch_task

    def _with_vulkan_context(self, func: Callable) -> Callable:
        """Wrap function with Vulkan context."""

        def fn(context: Context, **kwargs):
            if func.__code__.co_varnames[0] == "context":
                env = context.additional_metadata.get(POLICY_CONFIG_KEY)
                ctx = VulkanExecutionContext(
                    logger=context.logger if hasattr(context, "logger") else None,
                    env=env.variables if env else {},
                )
                return func(ctx, **kwargs)
            return func(**kwargs)

        return fn

    @classmethod
    def from_spec(cls, node: BranchNode):
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            func=node.func,
            choices=node.choices,
            dependencies=node.dependencies,
        )


class HatchetInput(InputNode, HatchetNode):
    """Hatchet implementation of InputNode."""

    def __init__(self, description: str, schema: dict[str, type], name="input_node"):
        super().__init__(name=name, description=description, schema=schema)

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], TaskOutput]:
        def input_task(
            workflow_input: TWorkflowInput, context: Context
        ) -> dict[str, Any]:
            # Return the workflow input data
            return TaskOutput(
                step_name=self.name,
                step_type=self.type.value,
                data=workflow_input.model_dump(),
            )

        return input_task

    @classmethod
    def from_spec(cls, node: InputNode):
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            schema=node.schema,
        )


class HatchetConnection(ConnectionNode, HatchetNode):
    """Hatchet implementation of ConnectionNode."""

    def __init__(
        self,
        name: str,
        url: str,
        method: str = "GET",
        description: str | None = None,
        headers: dict | None = None,
        params: dict | None = None,
        body: dict | None = None,
        timeout: int | None = None,
        retry_max_retries: int = 1,
        response_type: str = "JSON",
        dependencies: dict | None = None,
    ):
        super().__init__(
            name=name,
            url=url,
            method=method,
            description=description,
            headers=headers,
            params=params,
            body=body,
            timeout=timeout,
            retry_max_retries=retry_max_retries,
            response_type=response_type,
            dependencies=dependencies,
        )

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], TaskOutput]:
        def connection_task(
            workflow_input: TWorkflowInput, context: Context
        ) -> TaskOutput:
            env = context.additional_metadata.get(POLICY_CONFIG_KEY)
            inputs = self._get_parent_outputs(context)

            try:
                config = HTTPConfig(
                    url=self.url,
                    method=self.method,
                    headers=self.headers,
                    params=self.params,
                    body=self.body,
                    retry=RetryPolicy(max_retries=self.retry_max_retries),
                    response_type=self.response_type,
                )

                req = make_request(config, inputs, env.variables if env else {})
                response = requests.Session().send(req, timeout=self.timeout)

                # TODO: how should we log this to output, including on error?
                extra = {
                    "url": self.url,
                    "method": self.method,
                    "status_code": response.status_code,
                    "response_headers": dict(response.headers),
                }
                response.raise_for_status()

                if response.status_code == 200:
                    result = format_response_data(response.content, self.response_type)
                    return TaskOutput(
                        step_name=self.name,
                        step_type=self.type.value,
                        data=result,
                    )

            except (requests.exceptions.RequestException, HTTPError) as e:
                raise e
            except Exception as e:
                raise e

        return connection_task

    @classmethod
    def from_spec(cls, node: ConnectionNode):
        return cls(
            name=normalize_node_id(node.id),
            url=node.url,
            method=node.method,
            description=node.description,
            headers=node.headers,
            params=node.params,
            body=node.body,
            timeout=node.timeout,
            retry_max_retries=node.retry_max_retries,
            response_type=node.response_type,
            dependencies=node.dependencies,
        )


class HatchetDecision(DecisionNode, HatchetNode):
    """Hatchet implementation of DecisionNode."""

    def __init__(
        self,
        name: str,
        description: str,
        conditions: list[DecisionCondition],
        dependencies: dict[str, Any],
    ):
        super().__init__(
            name=name,
            description=description,
            conditions=conditions,
            dependencies=dependencies,
        )

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], TaskOutput]:
        def decision_task(
            workflow_input: TWorkflowInput, context: Context
        ) -> TaskOutput:
            inputs = self._get_parent_outputs(context)

            try:
                output = self._decision_fn(context, inputs)
                return TaskOutput(
                    step_name=self.name,
                    step_type=self.type.value,
                    data=output,
                )
            except Exception as e:
                raise UserCodeException(self.name) from e

        return decision_task

    def _decision_fn(self, context: Context, inputs: Dict[str, Any]) -> str:
        """Execute decision logic."""
        if_cond = next(c for c in self.conditions if c.decision_type == DecisionType.IF)
        else_cond = next(
            c for c in self.conditions if c.decision_type == DecisionType.ELSE
        )
        elif_conds = [
            c for c in self.conditions if c.decision_type == DecisionType.ELSE_IF
        ]

        if self._evaluate_condition(if_cond.condition, inputs):
            return if_cond.output
        for elif_cond in elif_conds:
            if self._evaluate_condition(elif_cond.condition, inputs):
                return elif_cond.output
        return else_cond.output

    def _evaluate_condition(self, condition: str, inputs: Dict[str, Any]) -> bool:
        """Evaluate a condition string."""
        norm_cond = normalize_to_template(condition)
        result = resolve_template(norm_cond, inputs, env_variables={})
        return result == "True"

    @classmethod
    def from_spec(cls, node: DecisionNode):
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            conditions=node.conditions,
            dependencies=node.dependencies,
        )


# Node type mapping
_NODE_TYPE_MAP: dict[type[Node], type[HatchetNode]] = {
    TransformNode: HatchetTransform,
    TerminateNode: HatchetTerminate,
    BranchNode: HatchetBranch,
    DataInputNode: HatchetDataInput,
    InputNode: HatchetInput,
    ConnectionNode: HatchetConnection,
    DecisionNode: HatchetDecision,
}


def to_hatchet_nodes(nodes: list[Node]) -> list[HatchetNode]:
    """Convert Vulkan nodes to Hatchet nodes."""
    return [to_hatchet_node(node) for node in nodes]


def to_hatchet_node(node: Node) -> HatchetNode:
    """Convert a single Vulkan node to a Hatchet node."""
    typ = type(node)
    impl_type = _NODE_TYPE_MAP.get(typ)
    if impl_type is None:
        msg = f"Node type {typ} has no known Hatchet implementation"
        raise ValueError(msg)

    return impl_type.from_spec(node)
