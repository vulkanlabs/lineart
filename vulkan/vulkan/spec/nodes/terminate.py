import json
import re
from enum import Enum
from typing import Any, Callable, cast

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
        return_metadata: dict[str, Dependency] | str | None = None,
        input_mode: str = "structured",
        description: str | None = None,
        callback: Callable | None = None,
        hierarchy: list[str] | None = None,
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
        return_metadata: dict | str, optional
            A dictionary of metadata that will be returned by the run, or a JSON string
            when input_mode is 'json'.
        input_mode: str, optional
            The input mode for metadata. Either 'structured' (default) or 'json'.
        description: str, optional
            A description of the node.
        callback: Callable, optional
            A callback that will be executed when the node is run.
            In the current implementation, the callback function always
            receives an execution context as its first argument.
            TODO: improve documentation on callback function signature.

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

        if input_mode not in ("structured", "json"):
            raise ValueError(
                f"Invalid input_mode: {input_mode}. Must be 'structured' or 'json'"
            )

        if return_metadata is not None:
            if input_mode == "structured":
                if not isinstance(return_metadata, dict):
                    raise TypeError(
                        f"Structured mode expects dict, got {type(return_metadata)}"
                    )
                if not all(isinstance(d, Dependency) for d in return_metadata.values()):
                    raise ValueError(
                        "Structured mode requires Dependency objects as values"
                    )
            elif input_mode == "json":
                if not isinstance(return_metadata, str):
                    raise TypeError(
                        f"JSON mode expects string, got {type(return_metadata)}"
                    )
                self._validate_json_metadata(return_metadata)

        self.return_metadata = return_metadata
        self.input_mode = input_mode

    def _validate_json_metadata(self, json_metadata: str) -> None:
        """Validate JSON syntax and template expressions like {{nodeId.field.subfield}}."""
        try:
            parsed = json.loads(json_metadata)

            if not isinstance(parsed, dict):
                raise ValueError("JSON metadata must be a dictionary at the root level")

            template_pattern = r"\{\{(\w+)(?:\.[\w\[\]\.]+)+\}\}"

            def validate_value(value, path=""):
                if isinstance(value, str):
                    malformed_patterns = [
                        r"\{\{[^}]*$",  # Unclosed braces
                        r"^[^{]*\}\}",  # Unmatched closing braces
                        r"\{\{[^.]*\}\}",  # Missing dot notation
                        r"\{\{\s*\}\}",  # Empty expression
                    ]

                    for pattern in malformed_patterns:
                        if re.search(pattern, value):
                            raise ValueError(
                                f"Malformed template expression in JSON metadata at path '{path}': {value}"
                            )

                    templates = re.findall(r"\{\{[^}]+\}\}", value)
                    for template in templates:
                        if not re.match(template_pattern, template):
                            raise ValueError(
                                f"Invalid template expression '{template}' at path '{path}'. Use format: {{{{nodeId.data.field}}}}"
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

    def node_definition(self) -> NodeDefinition:
        return NodeDefinition(
            name=self.name,
            description=self.description,
            node_type=self.type.value,
            dependencies=self.dependencies,
            metadata=TerminateNodeMetadata(
                return_status=self.return_status,
                return_metadata=self.return_metadata,
                input_mode=self.input_mode,
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
            input_mode=metadata.input_mode,
            hierarchy=definition.hierarchy,
        )
