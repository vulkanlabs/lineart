import json
from enum import Enum
from typing import Any, Callable, cast

from vulkan.node_config import (
    extract_env_vars_from_string,
    extract_runtime_params_from_string,
)
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes.base import Node, NodeDefinition, NodeType
from vulkan.spec.nodes.metadata import TerminateNodeMetadata


class TerminateNode(Node):
    """Marks the end of a workflow.

    Terminate nodes are used to mark the end of a workflow.
    They signal to the engine that the workflow has finished executing,
    and can be used to return a status code or a final decision, for example.

    Additionally, the user can specify a callback that will be executed
    when the node is run. This can be used to perform cleanup tasks, for example,
    or to communicate the final result of the workflow to an external system.

    All workflows must end with a terminate node, and all leaf nodes
    must be terminate nodes.
    This is currently not enforced, but it will be in the future.
    """

    def __init__(
        self,
        name: str,
        return_status: Enum | str,
        dependencies: dict[str, Dependency],
        return_metadata: str | None = None,
        description: str | None = None,
        callback: Callable | None = None,
        hierarchy: list[str] | None = None,
        parameters: dict[str, str] | None = None,
    ):
        """Marks the end of a workflow.

        Parameters
        ----------
        name : str
            The name of the node.
        return_status: Enum | str
            A "status" value that will be stored as the final status for the run.
        dependencies: dict, optional
            The dependencies of the node.
            See `Dependency` for more information.
        return_metadata: str, optional
            A JSON string of metadata that will be returned by the run.
            DEPRECATED: Use 'parameters' instead for better type safety and consistency.
        description: str, optional
            A description of the node.
        callback: Callable, optional
            A callback that will be executed when the node is run.
            In the current implementation, the callback function always
            receives an execution context as its first argument.
            TODO: improve documentation on callback function signature.
        parameters: dict[str, str], optional
            A dictionary of parameters that will be returned as metadata.
            Supports template expressions like '{{node.data.field}}'.
            This is the preferred way to pass metadata over return_metadata.

        """
        self.return_status = (
            return_status.value if isinstance(return_status, Enum) else return_status
        )
        if dependencies is None or len(dependencies) == 0:
            raise ValueError(f"Dependencies not set for TERMINATE op {name}")
        super().__init__(
            name=name,
            description=description,
            typ=NodeType.TERMINATE,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )
        self.callback = callback

        if return_metadata is not None:
            if not isinstance(return_metadata, str):
                raise TypeError(
                    f"return_metadata expects string, got {type(return_metadata)}"
                )
            self._validate_json_metadata(return_metadata)

        self.return_metadata = return_metadata
        self.parameters = parameters or {}

        # Validate parameters templates if provided
        if self.parameters:
            self._validate_parameters_templates(self.parameters)

    def _validate_json_metadata(self, json_metadata: str) -> None:
        """Validate JSON syntax and template expressions."""
        try:
            parsed = json.loads(json_metadata)

            if not isinstance(parsed, dict):
                raise ValueError("JSON metadata must be a dictionary at the root level")

            def validate_value(value, path=""):
                if isinstance(value, str):
                    try:
                        # Try to extract both runtime params and env vars to validate template syntax
                        extract_runtime_params_from_string(value)
                        extract_env_vars_from_string(value)
                    except ValueError as e:
                        raise ValueError(
                            f"Invalid template expression in JSON metadata at path '{path}': {value}. Error: {e}"
                        )

                elif isinstance(value, dict):
                    for k, v in value.items():
                        validate_value(v, f"{path}.{k}" if path else k)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        validate_value(item, f"{path}[{i}]" if path else f"[{i}]")

            validate_value(parsed)

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in return_metadata: {e}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Validation error in JSON metadata: {e}")

    def _validate_parameters_templates(self, parameters: dict[str, str]) -> None:
        """Validate template expressions in parameters dictionary."""
        for param_name, param_value in parameters.items():
            if isinstance(param_value, str):
                try:
                    # Try to extract both to validate template syntax
                    extract_runtime_params_from_string(param_value)
                    extract_env_vars_from_string(param_value)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid template expression in parameters at '{param_name}': {param_value}. Error: {e}"
                    )

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=TerminateNodeMetadata(
                return_status=self.return_status,
                return_metadata=self.return_metadata,
                parameters=self.parameters,
            ),
            hierarchy=self.hierarchy,
        )

    def with_callback(self, callback: Callable) -> "TerminateNode":
        self.callback = callback
        return self

    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "TerminateNode":
        definition = NodeDefinition.from_dict(spec)
        if definition.metadata is None:
            raise ValueError(f"Metadata not set for TERMINATE node {definition.name}")

        metadata = cast(TerminateNodeMetadata, definition.metadata)
        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            return_status=metadata.return_status,
            return_metadata=metadata.return_metadata,
            parameters=metadata.parameters,
            hierarchy=definition.hierarchy,
        )
