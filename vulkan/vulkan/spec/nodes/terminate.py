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
        description: str | None = None,
        callback: Callable | None = None,
        hierarchy: list[str] | None = None,
        output_data: dict[str, str] | None = None,
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
        description: str, optional
            A description of the node.
        callback: Callable, optional
            A callback that will be executed when the node is run.
            In the current implementation, the callback function always
            receives an execution context as its first argument.
            TODO: improve documentation on callback function signature.
        output_data: dict[str, str], optional
            Output data dict with template support. Converted to return_metadata for storage.

        """
        self.return_status = (
            return_status.value if isinstance(return_status, Enum) else return_status
        )
        if dependencies is None:
            dependencies = {}

        super().__init__(
            name=name,
            description=description,
            typ=NodeType.TERMINATE,
            dependencies=dependencies,
            hierarchy=hierarchy,
        )
        self.callback = callback

        # Store output_data and convert to return_metadata for serialization
        self.output_data = output_data or {}
        self.return_metadata = (
            self._output_data_to_metadata(self.output_data)
            if self.output_data
            else None
        )

        # Validate templates
        if self.output_data:
            self._validate_output_data_templates(self.output_data)

    def _validate_json_metadata(self, json_metadata: str) -> None:
        """Validate JSON and templates."""
        try:
            parsed = json.loads(json_metadata)

            if not isinstance(parsed, dict):
                raise ValueError("JSON metadata must be a dictionary at the root level")

            def validate_value(value, path=""):
                if isinstance(value, str):
                    try:
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

    def _validate_output_data_templates(self, output_data: dict[str, str]) -> None:
        """Validate templates in output_data."""
        for data_key, data_value in output_data.items():
            if isinstance(data_value, str):
                try:
                    extract_runtime_params_from_string(data_value)
                    extract_env_vars_from_string(data_value)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid template expression in output_data at '{data_key}': {data_value}. Error: {e}"
                    )

    def _output_data_to_metadata(self, output_data: dict[str, str]) -> str:
        """Convert output_data to JSON."""
        try:
            return json.dumps(output_data, sort_keys=True)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to convert output_data to JSON: {e}")

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=TerminateNodeMetadata(
                return_status=self.return_status,
                return_metadata=self.return_metadata,
                output_data=self.output_data,
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

        # Priority: output_data > return_metadata
        if metadata.output_data:
            output_data = metadata.output_data
        elif metadata.return_metadata:
            output_data = cls._metadata_to_output_data_static(metadata.return_metadata)
        else:
            output_data = {}

        return cls(
            name=definition.name,
            description=definition.description,
            dependencies=definition.dependencies,
            return_status=metadata.return_status,
            output_data=output_data,
            hierarchy=definition.hierarchy,
        )

    @staticmethod
    def _metadata_to_output_data_static(return_metadata: str) -> dict[str, str]:
        """Convert JSON metadata to output_data dict for deserialization."""
        try:
            parsed = json.loads(return_metadata)
            if not isinstance(parsed, dict):
                return {"value": str(parsed)}
            return {k: str(v) for k, v in parsed.items()}
        except (json.JSONDecodeError, Exception):
            return {}
