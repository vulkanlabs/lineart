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
                "output_data": {
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
                "output_data": {
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
        output_data={
            "message": "Test completed",
            "template_value": "{{input.data}}",
            "static_number": "42",
        },
    )

    # Verify storage
    assert node.output_data == {
        "message": "Test completed",
        "template_value": "{{input.data}}",
        "static_number": "42",
    }

    # Check serialization
    node_def = node.node_definition()
    assert node_def.metadata.output_data == node.output_data

    # Round-trip test
    spec_dict = node_def.to_dict()
    reconstructed_node = TerminateNode.from_dict(spec_dict)

    # Verify round-trip
    assert reconstructed_node.output_data == node.output_data
    assert reconstructed_node.name == node.name
    assert reconstructed_node.return_status == node.return_status


def test_terminate_node_parameter_to_metadata_conversion():
    """Test parameter to return_metadata conversion."""
    # Parameters are converted to return_metadata for serialization
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={"key": "{{input.data}}", "value": "test"},
    )

    # Parameters stored as-is, return_metadata generated as JSON
    assert node.output_data == {"key": "{{input.data}}", "value": "test"}
    assert node.return_metadata == '{"key": "{{input.data}}", "value": "test"}'


def test_terminate_node_dependencies_validation():
    """Test dependencies validation."""
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
    )
    assert node.name == "test_terminate"
    assert len(node.dependencies) == 1


def test_terminate_node_parameters_validation():
    """Test parameters validation."""
    # Valid parameters should work
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={"key": "value", "template": "{{input.data}}"},
    )
    assert node.output_data == {"key": "value", "template": "{{input.data}}"}
    assert node.return_metadata == '{"key": "value", "template": "{{input.data}}"}'


def test_terminate_node_template_validation():
    """Test template validation."""
    # Invalid template -> error
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            output_data={
                "invalid_template": "{{unclosed.template"
            },  # Missing closing braces
        )

    # Valid templates -> ok
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={"valid": "{{input.data}}", "also_valid": "{{input.nested.value}}"},
    )
    assert node.output_data is not None
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
    assert spec_dict["metadata"].get("output_data") == {}

    # Check minimal deserialization
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.name == "minimal_terminate"
    assert reconstructed.return_status == "DONE"
    assert reconstructed.return_metadata is None  # No parameters = no return_metadata
    assert reconstructed.output_data == {}

    # Full node
    node_full = TerminateNode(
        name="full_terminate",
        return_status="COMPLETE",
        dependencies={"input": Dependency("input_node")},
        description="Full featured terminate node",
        output_data={"extra": "data", "message": "All done"},
    )

    # Full round-trip
    spec_dict_full = node_full.node_definition().to_dict()
    reconstructed_full = TerminateNode.from_dict(spec_dict_full)

    assert reconstructed_full.name == node_full.name
    assert reconstructed_full.return_status == node_full.return_status
    assert reconstructed_full.description == node_full.description
    assert reconstructed_full.return_metadata == node_full.return_metadata
    assert reconstructed_full.output_data == node_full.output_data


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


def test_terminate_node_simple_parameters():
    """Test simple parameter handling."""
    # Simple parameters should work
    node = TerminateNode(
        name="simple_terminate",
        return_status="DONE",
        dependencies={"input": Dependency("input_node")},
        output_data={
            "status": "{{decision.final_status}}",
            "score": "{{risk.calculated_score}}",
            "static_info": "This is static",
        },
    )

    assert node.output_data == {
        "status": "{{decision.final_status}}",
        "score": "{{risk.calculated_score}}",
        "static_info": "This is static",
    }

    # Round-trip should preserve parameters
    spec_dict = node.node_definition().to_dict()
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.output_data == node.output_data


def test_terminate_node_parameters_template_validation():
    """Test parameters template validation."""
    # Invalid parameters template -> error
    with pytest.raises(ValueError, match="Invalid template expression"):
        TerminateNode(
            name="test_terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency("input_node")},
            output_data={
                "invalid": "{{bad..syntax}}"
            },  # Invalid template in parameters
        )

    # Valid parameters templates -> ok
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={
            "valid_simple": "{{input.data}}",
            "valid_nested": "{{input.nested.field}}",
            "static_value": "no template here",
        },
    )
    assert len(node.output_data) == 3


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
    # Empty parameters dict works
    node_empty_params = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={},
    )
    assert node_empty_params.output_data == {}
    assert node_empty_params.return_metadata is None  # No metadata for empty parameters

    # None parameters works (defaults to empty)
    node_no_params = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
    )
    assert node_no_params.output_data == {}
    assert node_no_params.return_metadata is None


def test_terminate_node_parameters_mixed_types():
    """Test parameters type handling."""
    # All values should be strings
    node = TerminateNode(
        name="test_terminate",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={
            "string_value": "hello",
            "number_as_string": "42",
            "boolean_as_string": "true",
            "template": "{{input.value}}",
            "json_like": '{"nested": "value"}',
        },
    )

    # Verify all strings
    assert all(isinstance(v, str) for v in node.output_data.values())
    assert node.output_data["number_as_string"] == "42"
    assert node.output_data["boolean_as_string"] == "true"
    assert node.output_data["json_like"] == '{"nested": "value"}'

    # Round-trip preserves types
    spec_dict = node.node_definition().to_dict()
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.output_data == node.output_data


def test_terminate_node_parameter_to_metadata_serialization():
    """Test parameters to return_metadata conversion for serialization."""

    # SDK path: parameters -> return_metadata
    sdk_node = TerminateNode(
        name="sdk_node",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={
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
    assert sdk_node.output_data == {
        "message": "User approved",
        "score": "85",
        "template": "{{input.data}}",
    }

    # Round-trip through serialization
    spec_dict = sdk_node.node_definition().to_dict()
    reconstructed = TerminateNode.from_dict(spec_dict)
    assert reconstructed.output_data == sdk_node.output_data


def test_terminate_node_backward_compatibility_deserialization():
    """Test deserializing old return_metadata format."""
    # Simulate old serialized format with return_metadata
    old_spec = {
        "name": "legacy_node",
        "node_type": "TERMINATE",
        "dependencies": {
            "input": {
                "node": "input_node",
                "output": None,
                "key": None,
                "hierarchy": None,
            }
        },
        "metadata": {
            "return_status": "SUCCESS",
            "return_metadata": '{"user": "John", "score": "95"}',
        },
    }

    # Should be able to deserialize and convert to parameters
    node = TerminateNode.from_dict(old_spec)
    assert node.output_data == {"user": "John", "score": "95"}
    # JSON is sorted by keys
    assert node.return_metadata == '{"score": "95", "user": "John"}'


def test_terminate_node_parameters_only():
    """Test that only parameters are accepted in constructor."""

    # Only parameters are used now
    node = TerminateNode(
        name="params_node",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={"source": "sdk", "value": "test"},
    )

    # Verify parameters are stored and converted to return_metadata
    assert node.output_data == {"source": "sdk", "value": "test"}
    assert node.return_metadata == '{"source": "sdk", "value": "test"}'


def test_terminate_node_parameter_type_handling():
    """Test parameter type handling."""

    # All parameter values should be strings
    node = TerminateNode(
        name="typed_node",
        return_status="SUCCESS",
        dependencies={"input": Dependency("input_node")},
        output_data={"string": "text", "template": "{{input.value}}"},
    )

    # Verify all stored as strings
    assert node.output_data == {"string": "text", "template": "{{input.value}}"}
    assert node.return_metadata == '{"string": "text", "template": "{{input.value}}"}'

    # Test deserialization from metadata with mixed types
    old_spec = {
        "name": "mixed_node",
        "node_type": "TERMINATE",
        "dependencies": {
            "input": {
                "node": "input_node",
                "output": None,
                "key": None,
                "hierarchy": None,
            }
        },
        "metadata": {
            "return_status": "SUCCESS",
            "return_metadata": '{"number": 42, "boolean": true, "string": "text"}',
        },
    }

    deserialized = TerminateNode.from_dict(old_spec)
    # Should convert all to strings (Python uses "True" for booleans)
    assert deserialized.output_data == {
        "number": "42",
        "boolean": "True",
        "string": "text",
    }
