import time
from abc import ABC, abstractmethod
from enum import Enum
from traceback import format_exception_only
from typing import Any, Callable

import requests
from dagster import In, OpDefinition, OpExecutionContext, Out, Output
from requests.exceptions import HTTPError

from vulkan.constants import POLICY_CONFIG_KEY
from vulkan.core.context import VulkanExecutionContext
from vulkan.core.run import RunStatus
from vulkan.core.step_metadata import StepMetadata
from vulkan.exceptions import UserCodeException
from vulkan.node_config import resolve_template
from vulkan.runners.dagster.io_manager import (
    METADATA_OUTPUT_KEY,
    PUBLISH_IO_MANAGER_KEY,
)
from vulkan.runners.dagster.resources import (
    DATA_CLIENT_KEY,
    RUN_CLIENT_KEY,
    VulkanDataClient,
    VulkanRunClient,
)
from vulkan.runners.dagster.run_config import (
    RUN_CONFIG_KEY,
    VulkanPolicyConfig,
    VulkanRunConfig,
)
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import (
    BranchNode,
    ConnectionNode,
    DataInputNode,
    InputNode,
    Node,
    TerminateNode,
    TransformNode,
)
from vulkan.spec.policy import PolicyDefinitionNode


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
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
            },
            required_resource_keys={DATA_CLIENT_KEY, POLICY_CONFIG_KEY, RUN_CONFIG_KEY},
        )

    def run(self, context, inputs):
        start_time = time.time()
        client: VulkanDataClient = getattr(context.resources, DATA_CLIENT_KEY)
        run_config: VulkanRunConfig = getattr(context.resources, RUN_CONFIG_KEY)
        extra = dict(data_source=self.data_source)
        error = None

        try:
            configured_params = self._get_configured_params(inputs)
            context.log.info(
                f"Fetching data from data source {self.data_source} with "
                f"parameters: {configured_params}"
            )

            response = client.get_data(
                data_source=self.data_source,
                configured_params=configured_params,
                run_id=run_config.run_id,
            )
            extra.update({"status_code": response.status_code})
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
        except (requests.exceptions.RequestException, HTTPError) as e:
            context.log.error(
                f"Failed request with status {response.status_code}: "
                f"{response.json().get('detail', '')}"
            )
            error = ("\n").join(format_exception_only(type(e), e))
            raise e
        except ValueError as e:
            context.log.error(f"Parameter resolution error: {str(e)}")
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

    def _get_configured_params(self, inputs):
        configured_params = {}
        try:
            for k, v in self.parameters.items():
                configured_params[k] = resolve_template(v, inputs, env_variables={})
        except Exception:
            raise ValueError(f"Invalid parameter configuration: {v}")
        return configured_params

    @classmethod
    def from_spec(cls, node: DataInputNode):
        return cls(
            name=node.name,
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
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
            },
            required_resource_keys={POLICY_CONFIG_KEY, RUN_CONFIG_KEY, RUN_CLIENT_KEY},
        )

    def run(self, context, inputs):
        start_time = time.time()
        client: VulkanRunClient = getattr(context.resources, RUN_CLIENT_KEY)

        body = inputs.get("body", None)

        error = None
        extra = dict()
        try:
            result = client.run_version_sync(
                policy_version_id=self.policy_id,
                data=body,
                time_step_ms=inputs.get("time_step_ms", 1000),
                timeout_ms=inputs.get("timeout_ms", 10000),
            )
            response_metadata = {
                "policy_version_id": self.policy_id,
                "run_id": result.get("run_id"),
                "success": result.get("success"),
            }
            extra.update({"response_metadata": response_metadata})
            yield Output(result["data"])
        except ValueError as e:
            context.log.error(f"Failed op {self.name}: {e}")
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
            name=node.name,
            policy_id=node.policy_id,
            dependencies=node.dependencies,
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
            name=node.name,
            description=node.description,
            func=node.func,
            dependencies=node.dependencies,
        )


class DagsterTerminate(TerminateNode, DagsterTransformNodeMixin):
    def __init__(
        self,
        name: str,
        description: str,
        return_status: UserStatus | str,
        dependencies: dict[str, Dependency],
        return_metadata: dict[str, Dependency] | None = None,
        callback: Callable | None = None,
    ):
        super().__init__(
            name=name,
            description=description,
            return_status=return_status,
            return_metadata=return_metadata,
            dependencies=dependencies,
            callback=callback,
        )
        self._func = self._fn

    def _fn(self, context, **kwargs):
        status = self.return_status
        result = status.value if isinstance(status, Enum) else status
        vulkan_run_config = context.resources.vulkan_run_config
        context.log.info(f"Terminating with status {status}")

        metadata = None
        if self.return_metadata is not None:
            metadata = {k: kwargs.get(k) for k in self.return_metadata.keys()}

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

    def _terminate(
        self,
        context: OpExecutionContext,
        result: str,
        metadata: dict[str, Any] | None = None,
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
                "metadata": metadata,
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
        dependencies = node.dependencies
        if node.return_metadata is not None:
            dependencies.update(node.return_metadata)

        return cls(
            name=node.name,
            description=node.description,
            return_status=node.return_status,
            return_metadata=node.return_metadata,
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
            name=node.name,
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


class DagsterConnection(ConnectionNode, DagsterNode):
    def __init__(
        self,
        name: str,
        url: str,
        method: str = "GET",
        description: str | None = None,
        headers: dict | None = None,
        path_params: list | None = None,
        query_params: dict | None = None,
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
            path_params=path_params,
            query_params=query_params,
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
                METADATA_OUTPUT_KEY: Out(io_manager_key=PUBLISH_IO_MANAGER_KEY),
            },
            required_resource_keys={RUN_CONFIG_KEY, POLICY_CONFIG_KEY},
        )

    def run(self, context, inputs):
        start_time = time.time()
        env: VulkanPolicyConfig = getattr(context.resources, POLICY_CONFIG_KEY)
        error = None
        extra = {}

        try:
            # Resolve headers, query params, and body
            headers = self._resolve_field(self.headers, inputs, env.variables)
            params = self._resolve_field(self.query_params, inputs, env.variables)
            data = (
                self._resolve_field(self.body, inputs, env.variables)
                if self.body
                else None
            )

            # TODO: Resolve URL with path parameters

            response = requests.request(
                method=self.method,
                url=self.url,
                headers=headers,
                params=params,
                json=data if data else None,
                timeout=self.timeout,
            )

            extra = {
                "url": self.url,
                "method": self.method,
                "status_code": response.status_code,
                "response_headers": dict(response.headers),
            }

            response.raise_for_status()

            # Parse response based on response_type
            if self.response_type.lower() == "json":
                result = response.json()
            elif self.response_type.lower() == "xml":
                result = response.text  # Could add XML parsing here
            elif self.response_type.lower() == "csv":
                result = response.text  # Could add CSV parsing here
            else:  # plain text or default
                result = response.text

            yield Output(result, output_name="result")

        except (requests.exceptions.RequestException, HTTPError) as e:
            context.log.error(f"Failed HTTP request in node {self.name}: {str(e)}")
            error = ("\n").join(format_exception_only(type(e), e))
            raise e
        except ValueError as e:
            context.log.error(
                f"Parameter resolution error in node {self.name}: {str(e)}"
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

    def _resolve_parameter_value(self, param_config, inputs, env_variables):
        """Resolve parameter value based on configuration type."""
        if isinstance(param_config, dict):
            if "variable" in param_config:
                # Runtime parameter from inputs
                var_name = param_config["variable"]
                if var_name not in inputs:
                    raise ValueError(
                        f"Runtime parameter '{var_name}' not found in inputs"
                    )

                if "key" in param_config:
                    # Access nested key from input
                    return inputs[var_name][param_config["key"]]
                else:
                    # Direct input value
                    return inputs[var_name]
            elif "env" in param_config:
                # Environment variable
                env_key = param_config["env"]
                if env_key not in env_variables:
                    raise ValueError(f"Environment variable '{env_key}' not found")
                return env_variables[env_key]
            elif "value" in param_config:
                # Fixed value (explicit)
                return param_config["value"]
            else:
                raise ValueError(f"Invalid parameter configuration: {param_config}")
        else:
            # Simple fixed value
            return param_config

    def _resolve_field(self, param_dict, inputs, env_variables):
        if not param_dict:
            return {}

        resolved = {}
        for key, config in param_dict.items():
            resolved[key] = self._resolve_parameter_value(config, inputs, env_variables)
        return resolved

    @classmethod
    def from_spec(cls, node: ConnectionNode):
        return cls(
            name=node.name,
            url=node.url,
            method=node.method,
            description=node.description,
            headers=node.headers,
            path_params=node.path_params,
            query_params=node.query_params,
            body=node.body,
            timeout=node.timeout,
            retry_max_retries=node.retry_max_retries,
            response_type=node.response_type,
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
