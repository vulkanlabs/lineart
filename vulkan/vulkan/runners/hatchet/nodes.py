import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict

import httpx
from hatchet_sdk import Context
from hatchet_sdk.runnables.types import TWorkflowInput
from pydantic import BaseModel

from vulkan.connections import (
    HTTPConfig,
    RetryPolicy,
    format_response_data,
)
from vulkan.core.context import VulkanExecutionContext
from vulkan.core.run import RunStatus
from vulkan.exceptions import UserCodeException
from vulkan.http_client import HTTPClient
from vulkan.node_config import resolve_value
from vulkan.runners.shared.app_client import BaseAppClient, create_app_client
from vulkan.runners.shared.constants import POLICY_CONFIG_KEY, RUN_CONFIG_KEY
from vulkan.runners.shared.decision_fn import evaluate_condition
from vulkan.runners.shared.run_config import VulkanPolicyConfig, VulkanRunConfig
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
            _workflow_input: TWorkflowInput, context: Context
        ) -> Dict[str, Any]:
            # Get resources from context
            run_cfg = context.additional_metadata.get(RUN_CONFIG_KEY)
            if not run_cfg:
                raise RuntimeError("Required resources not available in context")

            client: BaseAppClient = create_app_client(**run_cfg)
            inputs = self._get_parent_outputs(context)

            try:
                configured_params = self._get_configured_params(inputs)
                context.log(
                    f"Fetching data from data source {self.data_source} with "
                    f"parameters: {configured_params}"
                )

                response: httpx.Response = client.fetch_data(
                    data_source=self.data_source,
                    configured_params=configured_params,
                )

                response.raise_for_status()

                data = response.json()
                context.log(f"Data: {data}")

                response_metadata = {
                    "data_object_id": data.get("data_object_id"),
                    "request_key": data.get("key"),
                    "origin": data.get("origin"),
                }
                context.log(f"Response metadata: {response_metadata}")

                return TaskOutput(
                    step_name=self.name,
                    step_type=self.type.value,
                    data=data["value"],
                )

            except ValueError as e:
                context.log(f"Parameter resolution error: {str(e)}")
                raise e

            except httpx.HTTPStatusError as e:
                error_detail = "Unknown error"
                if hasattr(e, "response") and e.response is not None:
                    response = e.response
                    try:
                        error_detail = response.json().get("detail", str(e))
                    except Exception:
                        error_detail = (
                            response.text[:200] if hasattr(response, "text") else str(e)
                        )
                    context.log(
                        f"Failed request with status {response.status_code}: {error_detail}"
                    )
                else:
                    context.log(f"HTTP error: {str(e)}")
                raise e

            except httpx.HTTPError as e:
                context.log(f"Failed to retrieve data: {str(e)}")
                raise e

            except Exception as e:
                context.log(f"Unexpected error processing data: {str(e)}")
                raise e

        return data_input_task

    def _get_configured_params(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Get configured parameters with template resolution."""
        if self.parameters is None:
            return {}

        configured_params = {}
        for k, v in self.parameters.items():
            try:
                configured_params[k] = resolve_value(v, inputs, env_variables={})
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
        self._func = _with_vulkan_context(self.func)

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], Any]:
        def transform_task(_workflow_input: TWorkflowInput, context: Context) -> Any:
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

    def _get_configured_params(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Get configured parameters with template resolution."""
        if self.parameters is None:
            return {}

        configured_params = {}
        for k, v in self.parameters.items():
            try:
                configured_params[k] = resolve_value(v, inputs, env_variables={})
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
        def terminate_task(_workflow_input: TWorkflowInput, context: Context) -> str:
            inputs = self._get_parent_outputs(context)

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

        return terminate_task

    def _resolve_json_metadata(
        self, template_metadata: dict, inputs: dict, context: Context
    ) -> dict:
        """Resolve JSON metadata templates."""
        try:
            env_config = context.additional_metadata.get(POLICY_CONFIG_KEY)
            env_variables = env_config.variables if env_config else {}
        except Exception:
            env_variables = {}

        return resolve_value(template_metadata, inputs, env_variables)

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
        client: BaseAppClient = create_app_client(**run_config_dict)

        success = client.update_run_status(
            status=RunStatus.SUCCESS.value,
            result=result,
            metadata=metadata,
        )
        if not success:
            raise ValueError(f"Failed to terminate run {run_config.run_id}")

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
        self._func = _with_vulkan_context(self.func)

    @property
    def task_name(self) -> str:
        return self.name

    def task_fn(self) -> Callable[[TWorkflowInput, Context], Any]:
        def branch_task(_workflow_input: TWorkflowInput, context: Context) -> str:
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
            _workflow_input: TWorkflowInput, context: Context
        ) -> TaskOutput:
            env_cfg = context.additional_metadata.get(POLICY_CONFIG_KEY)
            env = VulkanPolicyConfig(**env_cfg)
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
                    timeout=self.timeout,
                )

                client = HTTPClient(config)
                response = client.execute_raw(inputs, env.variables if env else {})

                # TODO: how should we log this to output, including on error?
                # request details: extra={"url": self.url, "method": self.method, "status_code": response.status_code}
                response.raise_for_status()

                if response.status_code == 200:
                    result = format_response_data(response.content, self.response_type)
                    return TaskOutput(
                        step_name=self.name,
                        step_type=self.type.value,
                        data=result,
                    )

            except httpx.HTTPError as e:
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
            _workflow_input: TWorkflowInput, context: Context
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

        if evaluate_condition(if_cond.condition, inputs):
            return if_cond.output
        for elif_cond in elif_conds:
            if evaluate_condition(elif_cond.condition, inputs):
                return elif_cond.output
        return else_cond.output

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


def _with_vulkan_context(func: Callable) -> Callable:
    """Wrap function with Vulkan context."""

    def fn(context: Context, **kwargs):
        if func.__code__.co_varnames[0] == "context":
            env_cfg = context.additional_metadata.get(POLICY_CONFIG_KEY)
            env = VulkanPolicyConfig(**env_cfg)
            ctx = VulkanExecutionContext(
                logger=context.logger if hasattr(context, "logger") else None,
                env=env.variables if env else {},
            )
            return func(ctx, **kwargs)
        return func(**kwargs)

    return fn
