from enum import Enum

import pytest

from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import BranchNode, InputNode, NodeType, TerminateNode
from vulkan.spec.nodes.transform import TransformNode


class ExampleReturnStatus(Enum):
    SUCCESS = "SUCCESS"


TEST_TABLE = {
    "Input Node - Simple": (
        InputNode,
        {
            "name": INPUT_NODE,
            "node_type": NodeType.INPUT.value,
            "metadata": {
                "schema": {
                    "cpf": "str",
                },
            },
        },
    ),
    "Input Node - Complete": (
        InputNode,
        {
            "name": INPUT_NODE,
            "node_type": NodeType.INPUT.value,
            "description": "Optional node Description",
            "metadata": {
                "schema": {
                    "cpf": "str",
                    "score": "int",
                    "valid": "bool",
                    "test": "float",
                },
            },
        },
    ),
    "Branch Node - Simple": (
        BranchNode,
        {
            "name": "branch",
            "node_type": NodeType.BRANCH.value,
            "dependencies": {},
            "metadata": {
                "choices": ["A", "B"],
                "source_code": """
return 10**2
            """,
            },
        },
    ),
    "Branch Node - With Import": (
        BranchNode,
        {
            "name": "branch",
            "node_type": NodeType.BRANCH.value,
            "description": "Optional node Description",
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
            "metadata": {
                "choices": ["A", "B"],
                "source_code": """
import os
os.environ
            """,
            },
        },
    ),
    "Transform Node - Simple": (
        TransformNode,
        {
            "name": "transform",
            "node_type": NodeType.TRANSFORM.value,
            "dependencies": {},
            "metadata": {
                "source_code": """
return 10**2
            """,
            },
        },
    ),
    "Transform Node - With Import": (
        TransformNode,
        {
            "name": "transform",
            "node_type": NodeType.TRANSFORM.value,
            "description": "Optional node Description",
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
            "metadata": {
                "source_code": """
import os
os.environ
            """,
            },
        },
    ),
    "Terminate Node - Simple": (
        TerminateNode,
        {
            "name": "terminate_a",
            "node_type": NodeType.TERMINATE.value,
            "metadata": {
                "return_status": "SUCCESS",
            },
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
        },
    ),
    "Terminate Node - With Enum": (
        TerminateNode,
        {
            "name": "terminate_b",
            "node_type": NodeType.TERMINATE.value,
            "description": "Optional node Description",
            "metadata": {
                "return_status": ExampleReturnStatus.SUCCESS,
            },
            "dependencies": {
                "node_a": Dependency("node_a"),
            },
        },
    ),
    "Terminate Node - With Parameters": (
        TerminateNode,
        {
            "name": "terminate_with_params",
            "node_type": NodeType.TERMINATE.value,
            "description": "Terminate node with parameters",
            "metadata": {
                "return_status": "COMPLETED",
                "parameters": {
                    "message": "Task completed successfully",
                    "timestamp": "{{input.timestamp}}",
                    "user_id": "{{input.user_id}}",
                },
            },
            "dependencies": {
                "input": Dependency("input_node"),
            },
        },
    ),
    "Terminate Node - Mixed Parameters and Metadata": (
        TerminateNode,
        {
            "name": "terminate_mixed",
            "node_type": NodeType.TERMINATE.value,
            "description": "Terminate node with both parameters and metadata",
            "metadata": {
                "return_status": "SUCCESS",
                "return_metadata": '{"legacy_field": "{{input.data}}"}',
                "parameters": {
                    "new_field": "{{input.new_data}}",
                    "static_value": "constant",
                },
            },
            "dependencies": {
                "input": Dependency("input_node"),
            },
        },
    ),
    # TODO: Data input tests
}


@pytest.mark.parametrize(
    ["node_cls", "spec"],
    [(cls, spec) for cls, spec in TEST_TABLE.values()],
    ids=list(TEST_TABLE.keys()),
)
def test_node_from_spec(node_cls, spec):
    node = node_cls.from_dict(spec)
    assert node.name == spec["name"]
    assert node.type.value == spec["node_type"]
    assert node.description == spec.get("description", None)


def test_terminate_node_parameters():
    """Test parameters handling."""
    # Create with parameters
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        parameters={
            "message": "Test completed",
            "template_value": "{{input.data}}",
            "static_number": "42",
        },
    )

    # Verify storage
    assert node.parameters == {
        "message": "Test completed",
        "template_value": "{{input.data}}",
        "static_number": "42",
    }

    # Check serialization
    node_def = node.node_definition()
    assert node_def.metadata.parameters == node.parameters

    # Round-trip test
    spec_dict = node_def.to_dict()
    reconstructed_node = TerminateNode.from_dict(spec_dict)

    # Verify round-trip
    assert reconstructed_node.parameters == node.parameters
    assert reconstructed_node.name == node.name
    assert reconstructed_node.return_status == node.return_status


def test_terminate_node_backward_compatibility():
    """Test backward compatibility."""
    # Legacy usage: return_metadata only
    node_old = TerminateNode(
        name="test_terminate_old",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"legacy": "{{input.data}}"}',
    )

    # Bidirectional: JSON -> parameters
    assert node_old.parameters == {"legacy": "{{input.data}}"}
    assert node_old.return_metadata == '{"legacy": "{{input.data}}"}'

    # Mixed usage: both provided
    node_mixed = TerminateNode(
        name="test_terminate_mixed",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"legacy": "value"}',
        parameters={"new_param": "{{input.new_field}}"},
    )

    # Parameters wins over return_metadata
    assert node_mixed.parameters == {"new_param": "{{input.new_field}}"}
    assert (
        node_mixed.return_metadata == '{"new_param": "{{input.new_field}}"}'
    )  # Generated from parameters


def test_terminate_node_dependencies_validation():
    """Test dependencies validation."""
    # None dependencies -> error
    with pytest.raises(ValueError, match="Dependencies not set for TERMINATE op"):
        TerminateNode(name="test_terminate", return_status="SUCCESS", dependencies=None)

    # Empty dependencies -> error
    with pytest.raises(ValueError, match="Dependencies not set for TERMINATE op"):
        TerminateNode(name="test_terminate", return_status="SUCCESS", dependencies={})

    # Valid dependencies -> ok
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
    )
    assert node.name == "test_terminate"
    assert len(node.dependencies) == 1


def test_terminate_node_return_metadata_validation():
    """Test return_metadata validation."""
    # Wrong type -> error
    with pytest.raises(TypeError, match="return_metadata expects string"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata={"key": "value"},  # Dict instead of string
        )

    # Invalid JSON -> error
    with pytest.raises(ValueError, match="Invalid JSON in return_metadata"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"invalid": json}',  # Malformed JSON
        )

    # Non-dict JSON -> error
    with pytest.raises(
        ValueError, match="JSON metadata must be a dictionary at the root level"
    ):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='["array", "not", "dict"]',  # Array instead of dict
        )

    # String JSON -> error
    with pytest.raises(
        ValueError, match="JSON metadata must be a dictionary at the root level"
    ):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='"just a string"',  # String instead of dict
        )


def test_terminate_node_template_validation():
    """Test template validation."""
    # Invalid template -> error
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"invalid_template": "{{unclosed.template"}',  # Missing closing braces
        )

    # Nested invalid template -> error
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"nested": {"deep": {"invalid": "{{bad..syntax}}"}}}',  # Invalid template
        )

    # Array invalid template -> error
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"array": ["{{valid.template}}", "{{invalid..template}}"]}',  # Mixed valid/invalid
        )

    # Valid templates -> ok
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"valid": "{{input.data}}", "nested": {"also_valid": "{{input.nested.value}}"}}',
    )
    assert node.return_metadata is not None


def test_terminate_node_enum_return_status():
    """Test Enum return_status handling."""
    # Enum input
    node = TerminateNode(
        name="test_terminate",
        return_status=ExampleReturnStatus.SUCCESS,
        dependencies={"input": Dependency("input_node")},
    )

    # Extract string value
    assert node.return_status == "SUCCESS"
    assert isinstance(node.return_status, str)

    # Serialization preserves string
    node_def = node.node_definition()
    assert node_def.metadata.return_status == "SUCCESS"


def test_terminate_node_serialization_edge_cases():
    """Test serialization edge cases."""
    # Minimal node
    node_minimal = TerminateNode(
        name="minimal_terminate",
        return_status="DONE",
        dependencies={"input": Dependency("input_node")},
    )

    # Check minimal serialization
    spec_dict = node_minimal.node_definition().to_dict()
    assert spec_dict["name"] == "minimal_terminate"
    assert spec_dict["metadata"]["return_status"] == "DONE"
    assert spec_dict["metadata"].get("return_metadata") is None
    assert spec_dict["metadata"].get("parameters") == {}

    # Check minimal deserialization
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.name == "minimal_terminate"
    assert reconstructed.return_status == "DONE"
    assert reconstructed.return_metadata is None  # No parameters = no return_metadata
    assert reconstructed.parameters == {}

    # Full node
    node_full = TerminateNode(
        name="full_terminate",
        return_status="COMPLETE",
        dependencies={"input": Dependency("input_node")},
        description="Full featured terminate node",
        return_metadata='{"message": "All done"}',
        parameters={"extra": "data"},
    )

    # Full round-trip
    spec_dict_full = node_full.node_definition().to_dict()
    reconstructed_full = TerminateNode.from_dict(spec_dict_full)

    assert reconstructed_full.name == node_full.name
    assert reconstructed_full.return_status == node_full.return_status
    assert reconstructed_full.description == node_full.description
    assert reconstructed_full.return_metadata == node_full.return_metadata
    assert reconstructed_full.parameters == node_full.parameters


def test_terminate_node_from_dict_error_cases():
    """Test from_dict error cases."""
    # Missing metadata -> error
    invalid_spec_no_metadata = {
        "name": "test_terminate",
        "node_type": NodeType.TERMINATE.value,
        "dependencies": {"input": Dependency("input_node")},
        # Missing metadata key
    }

    with pytest.raises(ValueError, match="Metadata not set for TERMINATE node"):
        TerminateNode.from_dict(invalid_spec_no_metadata)

    # None metadata -> error
    invalid_spec_none_metadata = {
        "name": "test_terminate",
        "node_type": NodeType.TERMINATE.value,
        "dependencies": {"input": Dependency("input_node")},
        "metadata": None,
    }

    with pytest.raises(ValueError, match="Metadata not set for TERMINATE node"):
        TerminateNode.from_dict(invalid_spec_none_metadata)


def test_terminate_node_callback_handling():
    """Test callback handling."""
    # with_callback method
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
    )

    def test_callback(context):
        return "callback executed"

    # Returns self for chaining
    result = node.with_callback(test_callback)
    assert result is node

    # Callback is set
    assert node.callback == test_callback

    # Constructor callback
    node_with_callback = TerminateNode(
        name="test_terminate_cb",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        callback=test_callback,
    )

    assert node_with_callback.callback == test_callback


def test_terminate_node_complex_nested_structures():
    """Test complex nested JSON flattening."""
    complex_metadata = """{
        "result": {
            "status": "{{decision.final_status}}",
            "details": {
                "score": "{{risk.calculated_score}}",
                "factors": [
                    "{{factor1.value}}",
                    "static_factor",
                    "{{factor2.computed}}"
                ],
                "metadata": {
                    "timestamp": "{{system.timestamp}}",
                    "version": "1.0.0",
                    "nested_array": [
                        {"key": "{{nested.key1}}", "static": "value"},
                        {"key": "{{nested.key2}}", "number": 42}
                    ]
                }
            }
        },
        "static_info": "This is static",
        "array_of_objects": [
            {"template": "{{obj1.data}}", "static": "data1"},
            {"template": "{{obj2.data}}", "static": "data2"}
        ]
    }"""

    # Complex structure should work
    node = TerminateNode(
        name="complex_terminate",
        return_status="COMPLEX_DONE",
        dependencies={
            "decision": Dependency("decision_node"),
            "risk": Dependency("risk_node"),
            "factor1": Dependency("factor1_node"),
            "factor2": Dependency("factor2_node"),
            "system": Dependency("system_node"),
            "nested": Dependency("nested_node"),
            "obj1": Dependency("obj1_node"),
            "obj2": Dependency("obj2_node"),
        },
        return_metadata=complex_metadata,
    )

    assert node.return_metadata == complex_metadata

    # Round-trip complex structure
    spec_dict = node.node_definition().to_dict()
    reconstructed = TerminateNode.from_dict(spec_dict)

    # Check flattening worked
    expected_flattened = {
        "array_of_objects.0.static": "data1",
        "array_of_objects.0.template": "{{obj1.data}}",
        "array_of_objects.1.static": "data2",
        "array_of_objects.1.template": "{{obj2.data}}",
        "result.details.factors.0": "{{factor1.value}}",
        "result.details.factors.1": "static_factor",
        "result.details.factors.2": "{{factor2.computed}}",
        "result.details.metadata.nested_array.0.key": "{{nested.key1}}",
        "result.details.metadata.nested_array.0.static": "value",
        "result.details.metadata.nested_array.1.key": "{{nested.key2}}",
        "result.details.metadata.nested_array.1.number": "42",
        "result.details.metadata.timestamp": "{{system.timestamp}}",
        "result.details.metadata.version": "1.0.0",
        "result.details.score": "{{risk.calculated_score}}",
        "result.status": "{{decision.final_status}}",
        "static_info": "This is static",
    }
    assert reconstructed.parameters == expected_flattened


def test_terminate_node_parameters_template_validation():
    """Test parameters template validation."""
    # Invalid parameters template -> error
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            parameters={"invalid": "{{bad..syntax}}"},  # Invalid template in parameters
        )

    # Valid parameters templates -> ok
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        parameters={
            "valid_simple": "{{input.data}}",
            "valid_nested": "{{input.nested.field}}",
            "static_value": "no template here",
        },
    )
    assert len(node.parameters) == 3


def test_terminate_node_return_status_validation():
    """Test return_status edge cases."""
    # None return_status allowed
    node_none_status = TerminateNode(
        name="test_terminate",
        return_status=None,
        dependencies={"input": Dependency("input_node")},
    )
    assert node_none_status.return_status is None

    # Empty string allowed
    node_empty_status = TerminateNode(
        name="test_terminate",
        return_status="",
        dependencies={"input": Dependency("input_node")},
    )
    assert node_empty_status.return_status == ""

    # Valid string works
    node_valid = TerminateNode(
        name="test_terminate",
        return_status="COMPLETED",
        dependencies={"input": Dependency("input_node")},
    )
    assert node_valid.return_status == "COMPLETED"


def test_terminate_node_empty_collections():
    """Test empty values handling."""
    # Empty string -> error
    with pytest.raises(ValueError, match="Invalid JSON in return_metadata"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata="",  # Empty string is invalid JSON
        )

    # Empty JSON dict works
    node_minimal_json = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata="{}",  # Empty but valid JSON dict
    )
    assert node_minimal_json.return_metadata == "{}"

    # Empty parameters dict works
    node_empty_params = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        parameters={},
    )
    assert node_empty_params.parameters == {}


def test_terminate_node_parameters_mixed_types():
    """Test parameters type handling."""
    # All values should be strings
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        parameters={
            "string_value": "hello",
            "number_as_string": "42",
            "boolean_as_string": "true",
            "template": "{{input.value}}",
            "json_like": '{"nested": "value"}',
        },
    )

    # Verify all strings
    assert all(isinstance(v, str) for v in node.parameters.values())
    assert node.parameters["number_as_string"] == "42"
    assert node.parameters["boolean_as_string"] == "true"
    assert node.parameters["json_like"] == '{"nested": "value"}'

    # Round-trip preserves types
    spec_dict = node.node_definition().to_dict()
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.parameters == node.parameters


def test_terminate_node_bidirectional_conversion():
    """Test parameters <-> return_metadata conversion."""

    # SDK path: parameters -> return_metadata
    sdk_node = TerminateNode(
        name="sdk_node",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        parameters={
            "message": "User approved",
            "score": "85",
            "template": "{{input.data}}",
        },
    )

    # Auto-generate JSON from parameters
    assert (
        sdk_node.return_metadata
        == '{"message": "User approved", "score": "85", "template": "{{input.data}}"}'
    )
    assert sdk_node.parameters == {
        "message": "User approved",
        "score": "85",
        "template": "{{input.data}}",
    }

    # UI path: return_metadata -> parameters
    ui_node = TerminateNode(
        name="ui_node",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"result": "approved", "timestamp": "2023-01-01"}',
    )

    # Parse JSON to parameters dict
    assert (
        ui_node.return_metadata == '{"result": "approved", "timestamp": "2023-01-01"}'
    )
    assert ui_node.parameters == {"result": "approved", "timestamp": "2023-01-01"}


def test_terminate_node_complex_json_flattening():
    """Test nested JSON flattening with dot notation."""
    complex_json = """{
        "user": {"id": 123, "name": "John"},
        "scores": [85, 92, 78],
        "metadata": {"timestamp": "2023-01-01", "active": true},
        "nullable": null
    }"""

    node = TerminateNode(
        name="complex_node",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata=complex_json,
    )

    # Flatten to dot notation
    expected_params = {
        "user.id": "123",
        "user.name": "John",
        "scores.0": "85",
        "scores.1": "92",
        "scores.2": "78",
        "metadata.timestamp": "2023-01-01",
        "metadata.active": "true",
        "nullable": "null",
    }

    assert node.parameters == expected_params
    assert node.return_metadata == complex_json


def test_terminate_node_conversion_priority():
    """Test parameters takes precedence over return_metadata."""

    # Parameters wins when both provided
    node = TerminateNode(
        name="priority_node",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        parameters={"source": "sdk"},
        return_metadata='{"source": "ui"}',  # This should be ignored
    )

    # Verify parameters took precedence
    assert node.parameters == {"source": "sdk"}
    assert node.return_metadata == '{"source": "sdk"}'  # Generated from parameters


def test_terminate_node_edge_case_conversions():
    """Test conversion edge cases."""

    # Edge cases for conversion behavior

    # Mixed types in JSON
    node1 = TerminateNode(
        name="edge1",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"number": 42, "boolean": true, "string": "text"}',
    )
    expected_params1 = {"number": "42", "boolean": "true", "string": "text"}
    assert node1.parameters == expected_params1

    # Empty JSON
    node2 = TerminateNode(
        name="edge2",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata="{}",
    )
    assert node2.parameters == {}
    assert node2.return_metadata == "{}"

    # No metadata provided
    node3 = TerminateNode(
        name="edge3",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
    )
    # Empty state
    assert node3.parameters == {}
    assert node3.return_metadata is None
