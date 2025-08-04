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
    "Terminate Node - Mixed Parameters and Legacy Metadata": (
        TerminateNode,
        {
            "name": "terminate_mixed",
            "node_type": NodeType.TERMINATE.value,
            "description": "Terminate node with both parameters and legacy metadata",
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
    """Test that TerminateNode properly handles parameters."""
    # Test creating TerminateNode with parameters directly
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

    # Verify parameters are stored correctly
    assert node.parameters == {
        "message": "Test completed",
        "template_value": "{{input.data}}",
        "static_number": "42",
    }

    # Verify parameters are included in node definition
    node_def = node.node_definition()
    assert node_def.metadata.parameters == node.parameters

    # Test serialization and deserialization
    spec_dict = node_def.to_dict()
    reconstructed_node = TerminateNode.from_dict(spec_dict)

    # Verify parameters survive round-trip serialization
    assert reconstructed_node.parameters == node.parameters
    assert reconstructed_node.name == node.name
    assert reconstructed_node.return_status == node.return_status


def test_terminate_node_backward_compatibility():
    """Test that TerminateNode maintains backward compatibility."""
    # Test creating TerminateNode without parameters (old way)
    node_old = TerminateNode(
        name="test_terminate_old",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"legacy": "{{input.data}}"}',
    )

    # Should have empty parameters dict
    assert node_old.parameters == {}
    assert node_old.return_metadata == '{"legacy": "{{input.data}}"}'

    # Test creating TerminateNode with both (mixed mode)
    node_mixed = TerminateNode(
        name="test_terminate_mixed",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"legacy": "value"}',
        parameters={"new_param": "{{input.new_field}}"},
    )

    # Both should be preserved
    assert node_mixed.parameters == {"new_param": "{{input.new_field}}"}
    assert node_mixed.return_metadata == '{"legacy": "value"}'


def test_terminate_node_dependencies_validation():
    """Test that TerminateNode validates dependencies correctly."""
    # Test with None dependencies - should raise ValueError
    with pytest.raises(ValueError, match="Dependencies not set for TERMINATE op"):
        TerminateNode(name="test_terminate", return_status="SUCCESS", dependencies=None)

    # Test with empty dependencies - should raise ValueError
    with pytest.raises(ValueError, match="Dependencies not set for TERMINATE op"):
        TerminateNode(name="test_terminate", return_status="SUCCESS", dependencies={})

    # Test with valid dependencies - should work
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
    )
    assert node.name == "test_terminate"
    assert len(node.dependencies) == 1


def test_terminate_node_return_metadata_validation():
    """Test that TerminateNode validates return_metadata correctly."""
    # Test with invalid type for return_metadata - should raise TypeError
    with pytest.raises(TypeError, match="return_metadata expects string"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata={"key": "value"},  # Dict instead of string
        )

    # Test with invalid JSON - should raise ValueError
    with pytest.raises(ValueError, match="Invalid JSON in return_metadata"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"invalid": json}',  # Malformed JSON
        )

    # Test with non-dict JSON at root - should raise ValueError
    with pytest.raises(
        ValueError, match="JSON metadata must be a dictionary at the root level"
    ):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='["array", "not", "dict"]',  # Array instead of dict
        )

    # Test with string at root - should raise ValueError
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
    """Test that TerminateNode validates template expressions correctly."""
    # Test with invalid template syntax in return_metadata
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"invalid_template": "{{unclosed.template"}',  # Missing closing braces
        )

    # Test with invalid template in nested structure
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"nested": {"deep": {"invalid": "{{bad..syntax}}"}}}',  # Invalid template
        )

    # Test with invalid template in array
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata='{"array": ["{{valid.template}}", "{{invalid..template}}"]}',  # Mixed valid/invalid
        )

    # Test with valid templates - should work
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata='{"valid": "{{input.data}}", "nested": {"also_valid": "{{input.nested.value}}"}}',
    )
    assert node.return_metadata is not None


def test_terminate_node_enum_return_status():
    """Test that TerminateNode handles Enum return_status correctly."""
    # Test with Enum value
    node = TerminateNode(
        name="test_terminate",
        return_status=ExampleReturnStatus.SUCCESS,
        dependencies={"input": Dependency("input_node")},
    )

    # Should extract the string value from enum
    assert node.return_status == "SUCCESS"
    assert isinstance(node.return_status, str)

    # Test serialization preserves string value
    node_def = node.node_definition()
    assert node_def.metadata.return_status == "SUCCESS"


def test_terminate_node_serialization_edge_cases():
    """Test edge cases in serialization and deserialization."""
    # Test with None/empty optional fields
    node_minimal = TerminateNode(
        name="minimal_terminate",
        return_status="DONE",
        dependencies={"input": Dependency("input_node")},
    )

    # Verify minimal node serializes correctly
    spec_dict = node_minimal.node_definition().to_dict()
    assert spec_dict["name"] == "minimal_terminate"
    assert spec_dict["metadata"]["return_status"] == "DONE"
    assert spec_dict["metadata"].get("return_metadata") is None
    assert spec_dict["metadata"].get("parameters") == {}

    # Test deserialization of minimal node
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.name == "minimal_terminate"
    assert reconstructed.return_status == "DONE"
    assert reconstructed.return_metadata is None
    assert reconstructed.parameters == {}

    # Test with all fields populated
    node_full = TerminateNode(
        name="full_terminate",
        return_status="COMPLETE",
        dependencies={"input": Dependency("input_node")},
        description="Full featured terminate node",
        return_metadata='{"message": "All done"}',
        parameters={"extra": "data"},
    )

    # Round-trip serialization test
    spec_dict_full = node_full.node_definition().to_dict()
    reconstructed_full = TerminateNode.from_dict(spec_dict_full)

    assert reconstructed_full.name == node_full.name
    assert reconstructed_full.return_status == node_full.return_status
    assert reconstructed_full.description == node_full.description
    assert reconstructed_full.return_metadata == node_full.return_metadata
    assert reconstructed_full.parameters == node_full.parameters


def test_terminate_node_from_dict_error_cases():
    """Test error cases for from_dict method."""
    # Test with missing metadata
    invalid_spec_no_metadata = {
        "name": "test_terminate",
        "node_type": NodeType.TERMINATE.value,
        "dependencies": {"input": Dependency("input_node")},
        # Missing metadata key
    }

    with pytest.raises(ValueError, match="Metadata not set for TERMINATE node"):
        TerminateNode.from_dict(invalid_spec_no_metadata)

    # Test with None metadata
    invalid_spec_none_metadata = {
        "name": "test_terminate",
        "node_type": NodeType.TERMINATE.value,
        "dependencies": {"input": Dependency("input_node")},
        "metadata": None,
    }

    with pytest.raises(ValueError, match="Metadata not set for TERMINATE node"):
        TerminateNode.from_dict(invalid_spec_none_metadata)


def test_terminate_node_callback_handling():
    """Test callback functionality."""
    # Test with_callback method
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
    )

    def test_callback(context):
        return "callback executed"

    # Test that with_callback returns self (for chaining)
    result = node.with_callback(test_callback)
    assert result is node

    # Test that callback is set
    assert node.callback == test_callback

    # Test callback in constructor
    node_with_callback = TerminateNode(
        name="test_terminate_cb",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        callback=test_callback,
    )

    assert node_with_callback.callback == test_callback


def test_terminate_node_complex_nested_structures():
    """Test complex nested JSON structures with mixed templates."""
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

    # Should not raise any validation errors
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

    # Test serialization/deserialization of complex structure
    spec_dict = node.node_definition().to_dict()
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.return_metadata == complex_metadata


def test_terminate_node_parameters_template_validation():
    """Test template validation within parameters field."""
    # Test invalid template in parameters - should raise ValueError
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            parameters={"invalid": "{{bad..syntax}}"},  # Invalid template in parameters
        )

    # Test valid templates in parameters - should work
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
    """Test return_status validation edge cases."""
    # Test with None return_status - currently allowed by implementation
    node_none_status = TerminateNode(
        name="test_terminate",
        return_status=None,
        dependencies={"input": Dependency("input_node")},
    )
    assert node_none_status.return_status is None

    # Test with empty string return_status - should work (even if not ideal)
    node_empty_status = TerminateNode(
        name="test_terminate",
        return_status="",
        dependencies={"input": Dependency("input_node")},
    )
    assert node_empty_status.return_status == ""

    # Test with valid string return_status - should work
    node_valid = TerminateNode(
        name="test_terminate",
        return_status="COMPLETED",
        dependencies={"input": Dependency("input_node")},
    )
    assert node_valid.return_status == "COMPLETED"


def test_terminate_node_empty_collections():
    """Test behavior with empty collections and values."""
    # Test with empty string return_metadata - should raise ValueError (invalid JSON)
    with pytest.raises(ValueError, match="Invalid JSON in return_metadata"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            return_metadata="",  # Empty string is invalid JSON
        )

    # Test with minimal valid JSON metadata
    node_minimal_json = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        return_metadata="{}",  # Empty but valid JSON dict
    )
    assert node_minimal_json.return_metadata == "{}"

    # Test with empty parameters dict (should work fine)
    node_empty_params = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        parameters={},
    )
    assert node_empty_params.parameters == {}


def test_terminate_node_parameters_mixed_types():
    """Test parameters with different value types (all should be strings)."""
    # In the current implementation, parameters are expected to be strings
    # Test with various string representations
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

    # All should be preserved as strings
    assert all(isinstance(v, str) for v in node.parameters.values())
    assert node.parameters["number_as_string"] == "42"
    assert node.parameters["boolean_as_string"] == "true"
    assert node.parameters["json_like"] == '{"nested": "value"}'

    # Test serialization preserves string types
    spec_dict = node.node_definition().to_dict()
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.parameters == node.parameters
