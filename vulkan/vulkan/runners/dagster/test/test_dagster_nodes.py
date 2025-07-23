from enum import Enum

from vulkan.core.step_metadata import StepMetadata
from vulkan.runners.dagster.nodes import to_dagster_node
from vulkan.runners.dagster.testing import run_test_job
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import NodeType, TerminateNode, TransformNode


def test_dagster_transform():
    node = TransformNode(
        name="transform",
        description="Transform node",
        func=lambda context, inputs: inputs["x"] * 2,
        dependencies={"inputs": Dependency("input_node")},
    )

    assert len(node.dependencies) == 1

    dagster_node = to_dagster_node(node)
    dagster_op = dagster_node.op()
    assert len(dagster_op.ins) == 1
    assert set(dagster_op.outs.keys()) == {
        "result",
        "metadata",
    }, "Should have two outputs 'result' and 'metadata'"

    job_result = run_test_job(
        [node],
        input_schema={"x": int},
        run_config={"input_node": {"config": {"x": 10}}},
    )
    result = job_result._get_output_for_handle("transform", "result")
    assert result == 20
    metadata = job_result._get_output_for_handle("transform", "metadata")
    assert isinstance(metadata, StepMetadata)
    assert metadata.error is None


class ReturnStatus(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


def test_dagster_terminate():
    terminate = TerminateNode(
        name="terminate",
        description="Terminate node",
        return_status=ReturnStatus.APPROVED,
        dependencies={"inputs": Dependency("input_node")},
    )
    definition = terminate.node_definition()
    assert definition.node_type == NodeType.TERMINATE.value


def test_dagster_terminate_structured_metadata():
    """Test terminate node with structured metadata (default input_mode)."""
    return_metadata = {
        "decision": Dependency("decision_node"),
        "data": Dependency("input_node"),
    }
    terminate = TerminateNode(
        name="terminate",
        description="Terminate node with structured metadata",
        return_status=ReturnStatus.APPROVED,
        dependencies={"inputs": Dependency("input_node")},
        return_metadata=return_metadata,
        input_mode="structured",
    )
    definition = terminate.node_definition()
    assert definition.node_type == NodeType.TERMINATE.value
    assert definition.metadata.input_mode == "structured"
    assert definition.metadata.return_metadata == return_metadata


def test_dagster_terminate_json_metadata():
    """Test terminate node with JSON metadata."""
    json_metadata = '{"decision": "{{decision_node.data}}", "result": "{{input_node.data.value}}", "static": "approved"}'
    terminate = TerminateNode(
        name="terminate",
        description="Terminate node with JSON metadata",
        return_status=ReturnStatus.APPROVED,
        dependencies={"inputs": Dependency("input_node")},
        return_metadata=json_metadata,
        input_mode="json",
    )
    definition = terminate.node_definition()
    assert definition.node_type == NodeType.TERMINATE.value
    assert definition.metadata.input_mode == "json"
    assert definition.metadata.return_metadata == json_metadata


def test_dagster_terminate_json_validation():
    """Test JSON metadata validation."""
    import pytest

    # Test invalid JSON
    with pytest.raises(ValueError, match="Invalid JSON"):
        TerminateNode(
            name="terminate",
            description="Invalid JSON",
            return_status=ReturnStatus.APPROVED,
            dependencies={"inputs": Dependency("input_node")},
            return_metadata='{"invalid": json}',
            input_mode="json",
        )

    # Test invalid template expression (no dot notation)
    with pytest.raises(ValueError, match="Malformed template expression"):
        TerminateNode(
            name="terminate",
            description="Invalid template",
            return_status=ReturnStatus.APPROVED,
            dependencies={"inputs": Dependency("input_node")},
            return_metadata='{"invalid": "{{node}}"}',
            input_mode="json",
        )

    # Test malformed template
    with pytest.raises(ValueError, match="Malformed template expression"):
        TerminateNode(
            name="terminate",
            description="Malformed template",
            return_status=ReturnStatus.APPROVED,
            dependencies={"inputs": Dependency("input_node")},
            return_metadata='{"invalid": "{{node.data"}',
            input_mode="json",
        )


def test_dagster_terminate_json_template_resolution():
    """Test JSON template resolution with dynamic node IDs."""
    from vulkan.runners.dagster.nodes import DagsterTerminate

    # Create a JSON template that references specific node IDs
    json_metadata = '{"user_decision": "{{decision_node.data}}", "input_value": "{{data_input.data.value}}", "static_info": "processed"}'

    # Create terminate node with dependencies using different keys than the node IDs in templates
    terminate = TerminateNode(
        name="terminate",
        description="Terminate with JSON template resolution",
        return_status=ReturnStatus.APPROVED,
        dependencies={
            "decision_dep": Dependency("decision_node"),  # dependency key != node ID
            "input_dep": Dependency("data_input"),  # dependency key != node ID
        },
        return_metadata=json_metadata,
        input_mode="json",
    )

    # Convert to Dagster node
    dagster_terminate = DagsterTerminate.from_spec(terminate)

    # Test template resolution with mock data
    template_dict = {
        "user_decision": "{{decision_node.data}}",
        "input_value": "{{data_input.data.value}}",
        "static_info": "processed",
    }
    kwargs = {
        "decision_dep": {
            "data": "approved"
        },  # Data comes through dependency key, not node ID
        "input_dep": {"data": {"value": "test_data"}, "other": "ignored"},
    }

    resolved = dagster_terminate._resolve_json_metadata(template_dict, kwargs)

    expected = {
        "user_decision": "approved",
        "input_value": "test_data",
        "static_info": "processed",
    }

    assert resolved == expected


def test_dagster_terminate_all_template_formats():
    """Test all supported template formats in a single comprehensive test."""
    from vulkan.runners.dagster.nodes import DagsterTerminate

    # JSON with all different template formats
    json_metadata = """{
        "legacy_format": "{{nodeA.data.resourceB.key}}",
        "flexible_format": "{{consumer_id.name.credit_tax.score}}",
        "simple_reference": "{{decision_node.data}}",
        "deep_nesting": "{{user.profile.settings.preferences.theme}}"
    }"""

    terminate = TerminateNode(
        name="terminate_all_formats",
        description="Test all template formats",
        return_status=ReturnStatus.APPROVED,
        dependencies={
            "node_a_dep": Dependency("nodeA"),
            "consumer_dep": Dependency("consumer_id"),
            "decision_dep": Dependency("decision_node"),
            "user_dep": Dependency("user"),
        },
        return_metadata=json_metadata,
        input_mode="json",
    )

    dagster_terminate = DagsterTerminate.from_spec(terminate)

    # Mock data matching each template format
    template_dict = {
        "legacy_format": "{{nodeA.data.resourceB.key}}",
        "flexible_format": "{{consumer_id.name.credit_tax.score}}",
        "simple_reference": "{{decision_node.data}}",
        "deep_nesting": "{{user.profile.settings.preferences.theme}}",
    }

    kwargs = {
        "node_a_dep": {"data": {"resourceB": {"key": "legacy_value"}}},
        "consumer_dep": {"name": {"credit_tax": {"score": 785}}},
        "decision_dep": {"data": "approved"},
        "user_dep": {"profile": {"settings": {"preferences": {"theme": "dark_mode"}}}},
    }

    resolved = dagster_terminate._resolve_json_metadata(template_dict, kwargs)

    expected = {
        "legacy_format": "legacy_value",
        "flexible_format": "785",
        "simple_reference": "approved",
        "deep_nesting": "dark_mode",
    }

    assert resolved == expected


def test_dagster_terminate_input_mode_validation():
    """Test input_mode validation."""
    import pytest

    # Test invalid input_mode
    with pytest.raises(ValueError, match="Invalid input_mode"):
        TerminateNode(
            name="terminate",
            description="Invalid mode",
            return_status=ReturnStatus.APPROVED,
            dependencies={"inputs": Dependency("input_node")},
            input_mode="invalid",
        )

    # Test wrong metadata type for structured mode
    with pytest.raises(TypeError, match="Structured mode expects dict, got"):
        TerminateNode(
            name="terminate",
            description="Wrong metadata type",
            return_status=ReturnStatus.APPROVED,
            dependencies={"inputs": Dependency("input_node")},
            return_metadata='{"json": "string"}',
            input_mode="structured",
        )

    # Test wrong metadata type for json mode
    with pytest.raises(TypeError, match="JSON mode expects string, got"):
        TerminateNode(
            name="terminate",
            description="Wrong metadata type",
            return_status=ReturnStatus.APPROVED,
            dependencies={"inputs": Dependency("input_node")},
            return_metadata={"dict": Dependency("node")},
            input_mode="json",
        )
