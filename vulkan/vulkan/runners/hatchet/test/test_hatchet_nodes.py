from unittest.mock import patch

import pytest

from vulkan.runners.hatchet.nodes import (
    HatchetDataInput,
    HatchetTerminate,
    HatchetTransform,
    to_hatchet_nodes,
)
from vulkan.runners.hatchet.policy import HatchetFlow
from vulkan.runners.hatchet.run_config import HatchetPolicyConfig, HatchetRunConfig
from vulkan.runners.hatchet.workspace import HatchetClientConfig
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import (
    DataInputNode,
    TerminateNode,
    TransformNode,
)


class TestHatchetNodes:
    """Test Hatchet node implementations."""

    def test_data_input_node_conversion(self):
        """Test DataInputNode to HatchetDataInput conversion."""
        node = DataInputNode(
            name="test_data_input",
            data_source="test_source",
            description="Test data input",
            parameters={"param1": "value1"},
        )

        hatchet_node = HatchetDataInput.from_spec(node)

        assert hatchet_node.name == "test_data_input"
        assert hatchet_node.data_source == "test_source"
        assert hatchet_node.description == "Test data input"
        assert hatchet_node.parameters == {"param1": "value1"}
        assert hatchet_node.task_name == "test_data_input"
        assert callable(hatchet_node.task_fn())

    def test_transform_node_conversion(self):
        """Test TransformNode to HatchetTransform conversion."""

        def test_func(x):
            return x * 2

        node = TransformNode(
            name="test_transform",
            description="Test transform",
            func=test_func,
            dependencies={"input": Dependency(INPUT_NODE)},
        )

        hatchet_node = HatchetTransform.from_spec(node)

        assert hatchet_node.name == "test_transform"
        assert hatchet_node.description == "Test transform"
        assert hatchet_node.func == test_func
        assert hatchet_node.task_name == "test_transform"
        assert callable(hatchet_node.task_fn())

    def test_terminate_node_conversion(self):
        """Test TerminateNode to HatchetTerminate conversion."""
        node = TerminateNode(
            name="test_terminate",
            description="Test terminate",
            return_status="SUCCESS",
            dependencies={"input": Dependency(INPUT_NODE)},
        )

        hatchet_node = HatchetTerminate.from_spec(node)

        assert hatchet_node.name == "test_terminate"
        assert hatchet_node.description == "Test terminate"
        assert hatchet_node.return_status == "SUCCESS"
        assert hatchet_node.task_name == "test_terminate"
        assert callable(hatchet_node.task_fn())

    def test_to_hatchet_nodes(self):
        """Test conversion of multiple nodes."""
        nodes = [
            DataInputNode(name="data_input", data_source="test", dependencies={}),
            TransformNode(
                name="transform", description="test", func=lambda x: x, dependencies={}
            ),
            TerminateNode(
                name="terminate",
                description="test",
                return_status="SUCCESS",
                dependencies={},
            ),
        ]

        hatchet_nodes = to_hatchet_nodes(nodes)

        assert len(hatchet_nodes) == 3
        assert isinstance(hatchet_nodes[0], HatchetDataInput)
        assert isinstance(hatchet_nodes[1], HatchetTransform)
        assert isinstance(hatchet_nodes[2], HatchetTerminate)


class TestHatchetFlow:
    """Test HatchetFlow workflow creation."""

    def test_hatchet_flow_creation(self):
        """Test creating a HatchetFlow from nodes."""
        from vulkan.spec.nodes import InputNode

        nodes = [
            InputNode(name="input", description="Input node", schema={"test": str}),
            DataInputNode(name="data_input", data_source="test", dependencies={}),
            TransformNode(
                name="transform", description="test", func=lambda x: x, dependencies={}
            ),
            TerminateNode(
                name="terminate",
                description="test",
                return_status="SUCCESS",
                dependencies={},
            ),
        ]

        flow = HatchetFlow(nodes, "test_policy")

        assert flow.policy_name == "test_policy"
        assert len(flow.nodes) == 4
        assert flow.create_workflow() is not None

    def test_create_hatchet_workflow(self):
        """Test the create_hatchet_workflow helper function."""
        nodes = [
            DataInputNode(name="data_input", data_source="test"),
        ]

        flow = HatchetFlow(nodes, "test_workflow")

        assert isinstance(flow, HatchetFlow)
        assert flow.policy_name == "test_workflow"


class TestHatchetRunConfig:
    """Test Hatchet configuration classes."""

    def test_hatchet_run_config_creation(self):
        """Test HatchetRunConfig creation."""
        config = HatchetRunConfig(
            run_id="test_run",
            server_url="http://localhost:8000",
            hatchet_server_url="http://localhost:8080",
            hatchet_api_key="test_key",
            namespace="test_namespace",
        )

        assert config.run_id == "test_run"
        assert config.server_url == "http://localhost:8000"
        assert config.hatchet_server_url == "http://localhost:8080"
        assert config.hatchet_api_key == "test_key"
        assert config.namespace == "test_namespace"

    @patch.dict(
        "os.environ",
        {
            "HATCHET_SERVER_URL": "http://test:8080",
            "HATCHET_CLIENT_TOKEN": "test_client_token",
            "HATCHET_NAMESPACE": "test_ns",
        },
    )
    def test_hatchet_run_config_from_env(self):
        """Test HatchetRunConfig creation from environment."""
        config = HatchetRunConfig.from_env("test_run", "http://localhost:8000")

        assert config.run_id == "test_run"
        assert config.server_url == "http://localhost:8000"
        assert config.hatchet_server_url == "http://test:8080"
        assert config.hatchet_api_key == "test_client_token"
        assert config.namespace == "test_ns"

    def test_hatchet_policy_config(self):
        """Test HatchetPolicyConfig creation."""
        config = HatchetPolicyConfig.from_dict({"var1": "value1", "var2": "value2"})

        assert config.variables == {"var1": "value1", "var2": "value2"}


class TestHatchetClientConfig:
    """Test HatchetClientConfig."""

    def test_client_config_creation(self):
        """Test client config creation."""
        config = HatchetClientConfig(
            server_url="http://localhost:8080",
            token="test_token",
            namespace="test_namespace",
        )

        assert config.server_url == "http://localhost:8080"
        assert config.token == "test_token"
        assert config.namespace == "test_namespace"


if __name__ == "__main__":
    pytest.main([__file__])
