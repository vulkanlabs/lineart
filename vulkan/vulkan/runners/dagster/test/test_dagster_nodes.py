import logging
from enum import Enum
from unittest.mock import Mock

import httpx
import pytest
from vulkan.core.context import VulkanExecutionContext
from vulkan.runners.dagster.nodes import (
    DagsterDataInput,
    DagsterTerminate,
    to_dagster_node,
)
from vulkan.runners.shared.constants import APP_CLIENT_KEY
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import NodeType, TerminateNode, TransformNode


@pytest.fixture
def mock_context():
    return VulkanExecutionContext(logging.Logger("test"), {})


class ReturnStatus(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class TestTransformNode:
    """Test suite for TransformNode functionality."""

    def test_transform_node_creation_and_dagster_conversion(self):
        """Test TransformNode creation and conversion to Dagster."""
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
        }, "Should only a 'result' key"


class TestTerminateNode:
    """Test suite for TerminateNode functionality matching frontend usage."""

    def test_terminate_node_basic_creation(self):
        """Test basic TerminateNode creation and definition."""
        terminate = TerminateNode(
            name="terminate",
            description="Terminate node",
            return_status="success",
            dependencies={"inputs": Dependency("input_node")},
        )
        definition = terminate.node_definition()
        assert definition.node_type == NodeType.TERMINATE.value
        assert definition.metadata.return_status == "success"

    def test_terminate_node_with_string_return_statuses(self):
        """Test TerminateNode with different string return statuses (as frontend sends)."""
        test_statuses = ["success", "failed", "timeout", "approved", "denied"]

        for status in test_statuses:
            terminate = TerminateNode(
                name=f"terminate_{status}",
                description=f"Terminate node with {status} status",
                return_status=status,
                dependencies={"inputs": Dependency("input_node")},
            )
            definition = terminate.node_definition()
            assert definition.node_type == NodeType.TERMINATE.value
            assert definition.metadata.return_status == status

    def test_terminate_node_with_simple_json_metadata(self):
        """Test TerminateNode with simple parameters converted to JSON metadata."""
        terminate = TerminateNode(
            name="terminate_simple",
            description="Terminate node with output_data",
            return_status="success",
            dependencies={"inputs": Dependency("input_node")},
            output_data={"message": "Task completed successfully"},
        )
        definition = terminate.node_definition()
        assert (
            definition.metadata.return_metadata
            == '{"message": "Task completed successfully"}'
        )

    def test_terminate_node_with_json_string_metadata(self):
        """Test TerminateNode with JSON string metadata (as frontend sends)."""
        json_metadata = '{"items_processed": "42", "result": "completed", "timestamp": "2024-01-01T00:00:00Z"}'
        terminate = TerminateNode(
            name="terminate_json",
            description="Terminate node with JSON string metadata",
            return_status="success",
            dependencies={"inputs": Dependency("input_node")},
            output_data={
                "result": "completed",
                "items_processed": "42",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        )
        definition = terminate.node_definition()
        assert definition.metadata.return_metadata == json_metadata

    def test_terminate_node_with_simple_template(self):
        """Test TerminateNode with simple template variables (as shown in frontend)."""
        template_metadata = '{"decision": "{{decision_node.data}}", "user_input": "{{input_node.data}}"}'
        terminate = TerminateNode(
            name="terminate_template",
            description="Terminate node with template variables",
            return_status="success",
            dependencies={
                "decision": Dependency("decision_node"),
                "input": Dependency("input_node"),
            },
            output_data={
                "decision": "{{decision_node.data}}",
                "user_input": "{{input_node.data}}",
            },
        )
        definition = terminate.node_definition()
        assert definition.metadata.return_metadata == template_metadata

    def test_terminate_node_mixed_template_and_static(self):
        """Test mixing template variables with static text in JSON format."""
        mixed_metadata = '{"message": "User {{user_node.data}} completed task with status: approved"}'
        terminate = TerminateNode(
            name="terminate_mixed",
            description="Terminate node with mixed template and static text in JSON",
            return_status="success",
            dependencies={"user": Dependency("user_node")},
            output_data={
                "message": "User {{user_node.data}} completed task with status: approved"
            },
        )
        definition = terminate.node_definition()
        assert definition.metadata.return_metadata == mixed_metadata


class TestTerminateNodeTemplateResolution:
    """Test template resolution functionality that frontend users would actually use."""

    def test_simple_template_resolution(self, mock_context):
        """Test resolution of simple template variables."""
        terminate = TerminateNode(
            name="terminate_simple_template",
            description="Simple template resolution test",
            return_status="success",
            dependencies={"decision": Dependency("decision_node")},
            output_data={"decision": "{{decision.data}}", "status": "completed"},
        )

        dagster_terminate = DagsterTerminate.from_spec(terminate)

        template_dict = {
            "decision": "{{decision.data}}",
            "status": "completed",
        }

        kwargs = {
            "decision": {"data": "approved"},
        }

        resolved = dagster_terminate._resolve_json_metadata(
            template_dict, kwargs, mock_context
        )

        expected = {
            "decision": "approved",
            "status": "completed",
        }

        assert resolved == expected

    def test_multiple_template_variables(self, mock_context):
        """Test multiple template variables in metadata."""
        terminate = TerminateNode(
            name="terminate_multiple",
            description="Multiple template variables test",
            return_status="success",
            dependencies={
                "user": Dependency("user_node"),
                "task": Dependency("task_node"),
                "result": Dependency("result_node"),
            },
            output_data={
                "user": "{{user.data}}",
                "task": "{{task.data}}",
                "result": "{{result.data}}",
            },
        )

        dagster_terminate = DagsterTerminate.from_spec(terminate)

        template_dict = {
            "user": "{{user.data}}",
            "task": "{{task.data}}",
            "result": "{{result.data}}",
        }

        kwargs = {
            "user": {"data": "john_doe"},
            "task": {"data": "data_processing"},
            "result": {"data": "success"},
        }

        resolved = dagster_terminate._resolve_json_metadata(
            template_dict, kwargs, mock_context
        )

        expected = {
            "user": "john_doe",
            "task": "data_processing",
            "result": "success",
        }

        assert resolved == expected


class TestTerminateNodeValidation:
    """Test basic validation scenarios that matter for frontend usage."""

    def test_invalid_template_expression(self):
        """Test that invalid template expressions are caught."""
        with pytest.raises(ValueError, match="Invalid template expression"):
            TerminateNode(
                name="terminate",
                description="Invalid template test",
                return_status="success",
                dependencies={"inputs": Dependency("input_node")},
                output_data={"value": "{{node.data"},  # Missing closing brace
            )

    def test_wrong_output_data_type(self):
        """Test that non-dict output_data types cause AttributeError during validation."""
        with pytest.raises(AttributeError, match="object has no attribute 'items'"):
            TerminateNode(
                name="terminate",
                description="Wrong type test",
                return_status="success",
                dependencies={"inputs": Dependency("input_node")},
                output_data="should be dict",  # Should be dict
            )

    def test_unclosed_template_braces(self):
        """Test that malformed template expressions are caught."""
        with pytest.raises(ValueError, match="Invalid template expression"):
            TerminateNode(
                name="terminate",
                description="Malformed template test",
                return_status="success",
                dependencies={"inputs": Dependency("input_node")},
                output_data={"value": "{{node.data"},  # Missing closing brace
            )


class TestNodeTypeDefinitions:
    """Test node type definitions and basic integration."""

    def test_node_types(self):
        """Test that node types are correctly defined."""
        transform = TransformNode(
            name="transform",
            description="Transform node",
            func=lambda context, inputs: inputs,
            dependencies={"inputs": Dependency("input_node")},
        )

        terminate = TerminateNode(
            name="terminate",
            description="Terminate node",
            return_status="success",
            dependencies={"inputs": Dependency("input_node")},
        )

        assert transform.node_definition().node_type == NodeType.TRANSFORM.value
        assert terminate.node_definition().node_type == NodeType.TERMINATE.value


def _get_mock_op_context(response=None, fetch_error=None):
    """Create mock OpExecutionContext for testing."""
    context = Mock()
    context.log = Mock()
    context.log.info = print
    context.log.error = Mock()

    # Mock app client resource
    app_client = Mock()
    context.resources = Mock()

    if response is not None:
        app_client.fetch_data = Mock(return_value=response)
    if fetch_error is not None:
        app_client.fetch_data = Mock(side_effect=fetch_error)
    context.resources = Mock(
        **{APP_CLIENT_KEY: Mock(get_client=Mock(return_value=app_client))}
    )

    return context


class TestDagsterDataInput:
    """Test suite for DagsterDataInput error propagation and handling."""

    @pytest.fixture
    def data_input_node(self):
        """Create a DagsterDataInput instance for testing."""
        return DagsterDataInput(
            name="test_data_input",
            data_source="test_source",
            description="Test data input node",
            parameters={"param1": "value1"},
            dependencies={},
        )

    def test_successful_data_fetch_no_error(self, data_input_node):
        """Test successful data fetch sets error=None in metadata."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(
            return_value={
                "value": {"result": "success"},
                "data_object_id": "obj123",
                "key": "key123",
                "origin": "test",
            }
        )

        mock_op_context = _get_mock_op_context(mock_response)

        # Execute and collect outputs
        outputs = list(data_input_node.run(mock_op_context, {}))

        assert len(outputs) == 1

        # Check result output
        result_output = outputs[0]
        assert result_output.value == {"result": "success"}

    def test_http_error_with_json_detail(self, data_input_node):
        """Test HTTP error with JSON detail is properly extracted and propagated."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid parameters provided"}
        mock_response.text = '{"detail": "Invalid parameters provided"}'
        http_error = httpx.HTTPStatusError(
            "HTTP Error", request=Mock(), response=mock_response
        )
        http_error.response = mock_response

        mock_op_context = _get_mock_op_context(fetch_error=http_error)

        # Execute and expect HTTPStatusError to be raised
        with pytest.raises(httpx.HTTPStatusError):
            list(data_input_node.run(mock_op_context, {}))

        # Verify error was logged with detail
        mock_op_context.log.error.assert_called_once()
        error_call = mock_op_context.log.error.call_args[0][0]
        assert "Failed request with status 400" in error_call
        assert "Invalid parameters provided" in error_call

    def test_http_error_with_text_fallback(self, data_input_node):
        """Test HTTP error falls back to response.text when JSON parsing fails."""
        # Mock error response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Internal Server Error: Database connection failed"

        http_error = httpx.HTTPStatusError(
            "HTTP Error", request=Mock(), response=mock_response
        )
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_op_context = _get_mock_op_context(mock_response)

        # Execute and expect HTTPStatusError to be raised
        with pytest.raises(httpx.HTTPStatusError):
            list(data_input_node.run(mock_op_context, {}))

        # Verify error was logged with text (truncated to 200 chars)
        mock_op_context.log.error.assert_called_once()
        error_call = mock_op_context.log.error.call_args[0][0]
        assert "Failed request with status 500" in error_call
        assert "Internal Server Error" in error_call

    def test_http_error_without_response(self, data_input_node):
        """Test HTTP error without response object is handled."""
        # Mock error without response
        http_error = httpx.HTTPStatusError(
            "Connection failed", request=Mock(), response=Mock()
        )
        http_error.response = None

        mock_op_context = _get_mock_op_context(fetch_error=http_error)

        # Execute and expect HTTPStatusError to be raised
        with pytest.raises(httpx.HTTPStatusError):
            list(data_input_node.run(mock_op_context, {}))

        # Verify generic error was logged
        mock_op_context.log.error.assert_called_once()
        error_call = mock_op_context.log.error.call_args[0][0]
        assert "HTTP error" in error_call

    def test_request_exception_propagated(self, data_input_node):
        """Test HTTPError is properly logged and propagated."""
        mock_op_context = _get_mock_op_context(
            fetch_error=httpx.HTTPError("Network timeout")
        )

        # Execute and expect HTTPError to be raised
        with pytest.raises(httpx.HTTPError):
            list(data_input_node.run(mock_op_context, {}))

        # Verify error was logged
        mock_op_context.log.error.assert_called_once()
        error_call = mock_op_context.log.error.call_args[0][0]
        assert "Failed to retrieve data" in error_call

    def test_unexpected_exception_handled(self, data_input_node):
        """Test unexpected exceptions are caught and logged."""
        mock_op_context = _get_mock_op_context(
            fetch_error=RuntimeError("Unexpected error")
        )

        # Execute and expect exception to be raised
        with pytest.raises(RuntimeError):
            list(data_input_node.run(mock_op_context, {}))

        # Verify error was logged
        mock_op_context.log.error.assert_called_once()
        error_call = mock_op_context.log.error.call_args[0][0]
        assert "Unexpected error processing data" in error_call
