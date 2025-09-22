import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from vulkan.core.policy import Policy
from vulkan.runners.hatchet.policy import HatchetFlow
from vulkan.runners.hatchet.resources import HatchetClientResource
from vulkan.runners.hatchet.run_config import HatchetPolicyConfig, HatchetRunConfig
from vulkan.schemas import DataSourceSpec
from vulkan.spec.policy import PolicyDefinition

logger = logging.getLogger(__name__)


class HatchetRunResult(ABC):
    """Base class for Hatchet run results."""

    @property
    @abstractmethod
    def data(self):
        """Get result data."""
        pass

    @property
    @abstractmethod
    def metadata(self):
        """Get result metadata."""
        pass


class HatchetSingleRunResult(HatchetRunResult):
    """Result from a single Hatchet workflow run."""

    def __init__(self, workflow_run_id: str, client: HatchetClientResource):
        self.workflow_run_id = workflow_run_id
        self.client = client
        self._result = None
        self._metadata = None

    @property
    def data(self):
        """Get the workflow run result."""
        if self._result is None:
            self._result = self._fetch_result()
        return self._result

    @property
    def metadata(self):
        """Get workflow run metadata."""
        if self._metadata is None:
            self._metadata = self._fetch_metadata()
        return self._metadata

    def _fetch_result(self) -> Dict[str, Any]:
        """Fetch workflow result from Hatchet."""
        try:
            # Use Hatchet client to get workflow run result
            # This would need to be implemented based on Hatchet SDK API
            # For now, return a placeholder
            return {"status": "completed", "workflow_run_id": self.workflow_run_id}
        except Exception as e:
            logger.error(f"Failed to fetch result: {e}")
            return {"status": "error", "error": str(e)}

    def _fetch_metadata(self) -> Dict[str, Any]:
        """Fetch workflow metadata from Hatchet."""
        try:
            # Use Hatchet client to get workflow run metadata
            # This would need to be implemented based on Hatchet SDK API
            return {"workflow_run_id": self.workflow_run_id}
        except Exception as e:
            logger.error(f"Failed to fetch metadata: {e}")
            return {"error": str(e)}


class HatchetBatchRunResult(HatchetRunResult):
    """Result from a batch of Hatchet workflow runs."""

    def __init__(self, workflow_run_ids: list[str], client: HatchetClientResource):
        self.workflow_run_ids = workflow_run_ids
        self.client = client
        self._results = None

    @property
    def data(self):
        """Get batch results."""
        if self._results is None:
            self._results = self._fetch_batch_results()
        return self._results

    @property
    def metadata(self):
        """Get batch metadata."""
        return {
            "workflow_run_ids": self.workflow_run_ids,
            "count": len(self.workflow_run_ids),
        }

    def _fetch_batch_results(self) -> list[Dict[str, Any]]:
        """Fetch all workflow results."""
        results = []
        for run_id in self.workflow_run_ids:
            single_result = HatchetSingleRunResult(run_id, self.client)
            results.append(single_result.data)
        return results


class HatchetPolicyRunner:
    """Local runner for Hatchet workflows that manages the development experience."""

    def __init__(
        self,
        policy_definition: PolicyDefinition,
        hatchet_server_url: str,
        hatchet_api_key: str,
        server_url: str = "http://localhost:8000",
        namespace: str = "default",
    ):
        """Initialize the Hatchet policy runner.

        Args:
            policy_definition: The Vulkan policy to run
            hatchet_server_url: URL of the remote Hatchet server
            hatchet_api_key: API key for Hatchet server authentication
            server_url: URL of the Vulkan server (for data sources)
            namespace: Hatchet namespace to use
        """
        self.policy = Policy.from_definition(policy_definition)
        self.policy_definition = policy_definition
        self.server_url = server_url
        self.hatchet_server_url = hatchet_server_url
        self.hatchet_api_key = hatchet_api_key
        self.namespace = namespace

        # Create Hatchet workflow from the Policy (which includes the input node)
        self.hatchet_flow = HatchetFlow(self.policy.nodes, "default_policy")
        self.workflow = self.hatchet_flow.create_workflow()

        logger.info("Initialized HatchetPolicyRunner for policy")

    @classmethod
    def from_env(
        cls,
        policy_definition: PolicyDefinition,
        server_url: str = "http://localhost:8000",
    ) -> "HatchetPolicyRunner":
        """Create runner using environment variables for Hatchet configuration."""
        import os

        hatchet_api_key = os.getenv("HATCHET_CLIENT_TOKEN")
        if not hatchet_api_key:
            raise ValueError("HATCHET_CLIENT_TOKEN environment variable is required")

        # Server URL is optional - Hatchet SDK can extract it from token
        hatchet_server_url = os.getenv("HATCHET_SERVER_URL", "")
        namespace = os.getenv("HATCHET_NAMESPACE", "default")

        return cls(
            policy_definition=policy_definition,
            hatchet_server_url=hatchet_server_url,
            hatchet_api_key=hatchet_api_key,
            server_url=server_url,
            namespace=namespace,
        )

    def run(
        self,
        input_data: Dict[str, Any],
        data_sources: Optional[list[DataSourceSpec]] = None,
        config_variables: Optional[Dict[str, Any]] = None,
    ) -> HatchetSingleRunResult:
        """Run the policy once with given input data.

        Args:
            input_data: Input data for the workflow
            data_sources: Data source configurations
            config_variables: Environment variables for the policy

        Returns:
            HatchetSingleRunResult containing the workflow execution result
        """
        run_id = str(time.time()).replace(".", "")

        # Create run configuration
        run_config = HatchetRunConfig(
            run_id=run_id,
            server_url=self.server_url,
            hatchet_server_url=self.hatchet_server_url,
            hatchet_api_key=self.hatchet_api_key,
            project_id=self.namespace,
        )

        # Create policy configuration
        policy_config = HatchetPolicyConfig(variables=config_variables or {})

        # Create Hatchet client
        client = HatchetClientResource(run_config)

        try:
            logger.info(f"Starting Hatchet workflow run: {run_id}")

            # Deploy workflow if not already deployed
            self._ensure_workflow_deployed(client)

            # Create input for Hatchet workflow
            workflow_input = self._create_workflow_input(
                input_data, data_sources, config_variables
            )

            # Trigger workflow execution
            workflow_run_id = self._trigger_workflow(client, workflow_input)

            logger.info(f"Hatchet workflow run started: {workflow_run_id}")

            return HatchetSingleRunResult(workflow_run_id, client)

        except Exception as e:
            logger.error(f"Failed to run workflow: {e}")
            raise

    def run_batch(
        self,
        input_data_path: str,
        data_sources: Optional[list[DataSourceSpec]] = None,
        config_variables: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> HatchetBatchRunResult:
        """Run the policy for a batch of input data.

        Args:
            input_data_path: Path to file containing batch input data
            data_sources: Data source configurations
            config_variables: Environment variables for the policy
            run_id: Optional run ID for the batch

        Returns:
            HatchetBatchRunResult containing all workflow execution results
        """
        if run_id is None:
            run_id = str(time.time()).replace(".", "")

        # Load batch input data
        batch_inputs = self._load_batch_inputs(input_data_path)

        workflow_run_ids = []

        for i, input_data in enumerate(batch_inputs):
            single_run_id = f"{run_id}_{i}"
            try:
                result = self.run(input_data, data_sources, config_variables)
                workflow_run_ids.append(result.workflow_run_id)
            except Exception as e:
                logger.error(f"Failed to run batch item {i}: {e}")
                # Continue with other items

        return HatchetBatchRunResult(
            workflow_run_ids,
            HatchetClientResource(
                HatchetRunConfig(
                    run_id=run_id,
                    server_url=self.server_url,
                    hatchet_server_url=self.hatchet_server_url,
                    hatchet_api_key=self.hatchet_api_key,
                    project_id=self.namespace,
                )
            ),
        )

    def _ensure_workflow_deployed(self, client: HatchetClientResource):
        """Ensure the workflow is deployed to Hatchet."""
        # This would check if the workflow is already deployed and deploy if needed
        # For now, we'll assume it's handled by the Hatchet SDK
        pass

    def _create_workflow_input(
        self,
        input_data: Dict[str, Any],
        data_sources: Optional[list[DataSourceSpec]] = None,
        config_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create input data structure for Hatchet workflow."""
        return {
            "input_data": input_data,
            "data_sources": [ds.model_dump() for ds in (data_sources or [])],
            "config_variables": config_variables or {},
        }

    def _trigger_workflow(
        self, client: HatchetClientResource, workflow_input: Dict[str, Any]
    ) -> str:
        """Trigger workflow execution on Hatchet."""
        try:
            # Use Hatchet client to trigger workflow
            # This would need to be implemented based on Hatchet SDK API
            # For now, return a mock workflow run ID
            workflow_run_id = f"wr_{int(time.time())}"
            logger.info(f"Triggered workflow with run ID: {workflow_run_id}")
            return workflow_run_id
        except Exception as e:
            logger.error(f"Failed to trigger workflow: {e}")
            raise

    def _load_batch_inputs(self, input_data_path: str) -> list[Dict[str, Any]]:
        """Load batch input data from file."""
        import os

        import pandas as pd

        if not os.path.exists(input_data_path):
            raise ValueError(f"Input data file not found: {input_data_path}")

        # Support different file formats
        if input_data_path.endswith(".parquet"):
            df = pd.read_parquet(input_data_path)
        elif input_data_path.endswith(".csv"):
            df = pd.read_csv(input_data_path)
        elif input_data_path.endswith(".json"):
            with open(input_data_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return [data]
        else:
            raise ValueError(f"Unsupported file format: {input_data_path}")

        return df.to_dict(orient="records")
