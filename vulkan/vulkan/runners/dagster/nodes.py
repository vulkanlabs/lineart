import json
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable

import httpx
from dagster import In, OpDefinition, OpExecutionContext, Out, Output

from vulkan.connections import (
    HTTPConfig,
    RetryPolicy,
    format_response_data,
)
from vulkan.core.context import VulkanExecutionContext
from vulkan.core.run import RunStatus
from vulkan.exceptions import UserCodeException
from vulkan.http_client import HTTPClient
from vulkan.node_config import resolve_template, resolve_value
from vulkan.runners.dagster.names import normalize_dependencies, normalize_node_id
from vulkan.runners.dagster.resources import AppClientResource
from vulkan.runners.shared.constants import (
    APP_CLIENT_KEY,
    POLICY_CONFIG_KEY,
    RUN_CONFIG_KEY,
)
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
from vulkan.spec.policy import PolicyDefinitionNode


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

    def op(self) -> OpDefinition:
        return OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                "result": Out(),
            },
            required_resource_keys={APP_CLIENT_KEY, POLICY_CONFIG_KEY, RUN_CONFIG_KEY},
        )

    def run(self, context: OpExecutionContext, inputs: dict[str, Any]):
        app_client_resource: AppClientResource = getattr(
            context.resources, APP_CLIENT_KEY
        )
        client = app_client_resource.get_client()
        inputs = _resolved_inputs(inputs, self.dependencies)

        try:
            configured_params = self._get_configured_params(inputs)
            context.log.info(
                f"Fetching data from data source {self.data_source} with "
                f"parameters: {configured_params}"
            )

            response = client.fetch_data(
                data_source=self.data_source,
                configured_params=configured_params,
            )

            response.raise_for_status()

            data = response.json()
            context.log.info(f"Data: {data}")

            yield Output(data["value"])

        except ValueError as e:
            context.log.error(f"Parameter resolution error: {str(e)}")
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
                context.log.error(
                    f"Failed request with status {response.status_code}: {error_detail}"
                )
            else:
                context.log.error(f"HTTP error: {str(e)}")

            raise e

        except httpx.HTTPError as e:
            context.log.error(f"Failed to retrieve data: {str(e)}")
            raise e

        except Exception as e:
            context.log.error(f"Unexpected error processing data: {str(e)}")
            raise e

    def _get_configured_params(self, inputs):
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


class DagsterPolicy(PolicyDefinitionNode, DagsterNode):
    def __init__(
        self,
        name: str,
        policy_id: str,
        dependencies: dict | None = None,
    ):
        super().__init__(
            name=name,
            policy_id=policy_id,
            dependencies=dependencies,
        )

    def op(self) -> OpDefinition:
        return OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                "result": Out(),
            },
            required_resource_keys={APP_CLIENT_KEY, POLICY_CONFIG_KEY, RUN_CONFIG_KEY},
        )

    def run(self, context: OpExecutionContext, inputs: dict[str, Any]):
        app_client_resource: AppClientResource = getattr(
            context.resources, APP_CLIENT_KEY
        )
        client = app_client_resource.get_client()
        inputs = _resolved_inputs(inputs, self.dependencies)

        # TODO: handle schema same way as data input nodes
        input_data = inputs.get("body", None)
        body = {"input_data": input_data}

        try:
            result = client.run_version_sync(
                policy_version_id=self.policy_id,
                data=body,
            )
            yield Output(result)
        except ValueError as e:
            context.log.error(f"Failed op {self.name}: {e}")
            raise e

    @classmethod
    def from_spec(cls, node: PolicyDefinitionNode):
        return cls(
            name=normalize_node_id(node.id),
            policy_id=node.policy_id,
            dependencies=node.dependencies,
        )


class DagsterTransformNodeMixin(DagsterNode):
    def op(self) -> OpDefinition:
        def fn(context, inputs):
            inputs = _resolved_inputs(inputs, self.dependencies)
            configured_params = self._get_configured_params(inputs)
            try:
                fn_params = {**inputs, **configured_params}
                result = self._func(context, **fn_params)
                yield Output(result, output_name="result")
            except Exception as e:
                raise UserCodeException(self.name) from e

        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                "result": Out(),
            },
            # We expose the configuration in transform nodes
            # to allow the callback function in terminate nodes to
            # access it. In the future, we may separate terminate nodes.
            required_resource_keys={APP_CLIENT_KEY, RUN_CONFIG_KEY, POLICY_CONFIG_KEY},
        )

        return node_op

    def _get_configured_params(self, inputs):
        params = getattr(self, "parameters", None)
        if params is None:
            return {}

        configured_params = {}
        for k, v in params.items():
            try:
                configured_params[k] = resolve_value(v, inputs, env_variables={})
            except Exception:
                raise ValueError(f"Invalid parameter configuration: {v}")
        return configured_params


def _with_vulkan_context(func: callable) -> callable:
    def fn(context: OpExecutionContext, **kwargs):
        if func.__code__.co_varnames[0] == "context":
            env = getattr(context.resources, POLICY_CONFIG_KEY)
            ctx = VulkanExecutionContext(logger=context.log, env=env.variables)
            return func(ctx, **kwargs)
        return func(**kwargs)

    return fn


def _resolved_inputs(
    inputs: dict[str, Any], dependencies: dict[str, Any]
) -> dict[str, Any]:
    resolved_inputs = {}
    for k, v in inputs.items():
        dep = dependencies.get(k)
        if dep is not None and dep.key is not None:
            resolved_inputs[k] = v[dep.key]
        else:
            resolved_inputs[k] = v
    return resolved_inputs


class DagsterTransform(TransformNode, DagsterTransformNodeMixin):
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

    @classmethod
    def from_spec(cls, node: TransformNode):
        # This is only necessary here, as TransformNodes are the only
        # type that can depend on internal nodes.
        deps = normalize_dependencies(node.dependencies)
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            func=node.func,
            dependencies=deps,
            parameters=node.parameters,
        )


class DagsterTerminate(TerminateNode, DagsterTransformNodeMixin):
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
            output_data=output_data,
            dependencies=dependencies,
            callback=callback,
        )
        self._func = self._fn

    def _fn(self, context: OpExecutionContext, **kwargs):
        status = self.return_status
        result = status.value if isinstance(status, Enum) else status
        vulkan_run_config: VulkanRunConfig = getattr(context.resources, RUN_CONFIG_KEY)
        context.log.debug(f"Terminating with status {status}")

        metadata = None
        if self.return_metadata is not None:
            try:
                template_metadata = json.loads(self.return_metadata)
                metadata = self._resolve_json_metadata(
                    template_metadata, kwargs, context
                )
            except json.JSONDecodeError as e:
                context.log.error(f"Failed to parse JSON metadata: {e}")
                raise ValueError(f"Invalid JSON in return_metadata: {e}")
            except Exception as e:
                context.log.error(f"Failed to resolve JSON metadata: {e}")
                raise ValueError(f"Failed to resolve JSON metadata: {e}")

        terminated = self._terminate(context, result, metadata)
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

    def _resolve_json_metadata(
        self,
        template_metadata: dict,
        kwargs: dict,
        context: VulkanExecutionContext,
    ) -> dict:
        """Replace template expressions with actual node data using Jinja2."""
        try:
            env_config = getattr(context.resources, POLICY_CONFIG_KEY, None)
            env_variables = env_config.variables if env_config else {}
        except Exception:
            env_variables = {}

        return resolve_value(template_metadata, kwargs, env_variables)

    def _terminate(
        self,
        context: OpExecutionContext,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        app_client_resource: AppClientResource = getattr(
            context.resources, APP_CLIENT_KEY
        )
        client = app_client_resource.get_client()
        backend_run_id: str = context.run_id

        context.log.debug(f"Returning status {result} for Dagster run {backend_run_id}")

        success = client.update_run_status(
            status=RunStatus.SUCCESS.value,
            result=result,
            metadata=metadata,
        )

        if not success:
            context.log.error(
                f"Failed to return status {result} for Dagster run {backend_run_id}"
            )

        return success

    @classmethod
    def from_spec(cls, node: TerminateNode):
        dependencies = node.dependencies

        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            return_status=node.return_status,
            output_data=node.output_data,
            dependencies=dependencies,
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
            inputs = _resolved_inputs(inputs, self.dependencies)
            try:
                output = self._func(context, **inputs)
                yield Output(None, output)
            except Exception as e:
                raise UserCodeException(self.name) from e

        branch_paths = {out: Out(is_required=False) for out in self.choices}
        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                **branch_paths,
            },
            required_resource_keys={POLICY_CONFIG_KEY},
        )
        return node_op

    @classmethod
    def from_spec(cls, node: BranchNode):
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            func=node.func,
            choices=node.choices,
            dependencies=node.dependencies,
        )


class DagsterInput(InputNode, DagsterNode):
    def __init__(self, description: str, schema: dict[str, type], name="input_node"):
        super().__init__(name=name, description=description, schema=schema)

    def run(self, context, *args, **kwargs):
        config = context.op_config
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
            name=normalize_node_id(node.id),
            description=node.description,
            schema=node.schema,
        )


class DagsterConnection(ConnectionNode, DagsterNode):
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

    def op(self) -> OpDefinition:
        return OpDefinition(
            compute_fn=self.run,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                "result": Out(),
            },
            required_resource_keys={RUN_CONFIG_KEY, POLICY_CONFIG_KEY},
        )

    def run(self, context, inputs):
        env: VulkanPolicyConfig = getattr(context.resources, POLICY_CONFIG_KEY)
        inputs = _resolved_inputs(inputs, self.dependencies)

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
            response = client.execute_raw(inputs, env.variables)

            response.raise_for_status()

            if response.status_code == 200:
                result = format_response_data(response.content, self.response_type)
                yield Output(result)
        except httpx.HTTPError as e:
            context.log.error(f"Failed HTTP request: {str(e)}")
            raise e
        except Exception as e:
            context.log.error(str(e))
            raise e

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


class DagsterDecision(DecisionNode, DagsterNode):
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

    def _decision_fn(self, context, inputs):
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

    def op(self) -> OpDefinition:
        def fn(context, inputs):
            inputs = _resolved_inputs(inputs, self.dependencies)
            try:
                output = self._decision_fn(context, inputs)
                yield Output(None, output)
            except Exception as e:
                raise UserCodeException(self.name) from e

        branch_paths = {
            condition.output: Out(is_required=False) for condition in self.conditions
        }
        node_op = OpDefinition(
            compute_fn=fn,
            name=self.name,
            ins={k: In() for k in self.dependencies.keys()},
            outs={
                **branch_paths,
            },
            required_resource_keys={POLICY_CONFIG_KEY},
        )
        return node_op

    @classmethod
    def from_spec(cls, node: DecisionNode):
        return cls(
            name=normalize_node_id(node.id),
            description=node.description,
            conditions=node.conditions,
            dependencies=node.dependencies,
        )


_NODE_TYPE_MAP: dict[type[Node], type[DagsterNode]] = {
    TransformNode: DagsterTransform,
    TerminateNode: DagsterTerminate,
    BranchNode: DagsterBranch,
    DataInputNode: DagsterDataInput,
    InputNode: DagsterInput,
    PolicyDefinitionNode: DagsterPolicy,
    ConnectionNode: DagsterConnection,
    DecisionNode: DagsterDecision,
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
