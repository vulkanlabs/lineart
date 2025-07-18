"""
Policy version management service.

Handles all business logic related to policy versions including CRUD operations,
workspace management, configuration variables, data source dependencies, and run execution.
"""

from datetime import date
from typing import Any

from sqlalchemy import func as F
from sqlalchemy import select
from sqlalchemy.orm import Session

from vulkan.spec.nodes.base import NodeType
from vulkan_engine import schemas
from vulkan_engine.dagster.launch_run import DagsterRunLauncher, get_run_result
from vulkan_engine.db import (
    ConfigurationValue,
    DataSource,
    Policy,
    PolicyVersion,
    Run,
    WorkflowDataDependency,
)
from vulkan_engine.events import VulkanEvent
from vulkan_engine.exceptions import (
    DataSourceNotFoundException,
    InvalidDataSourceException,
    PolicyVersionInUseException,
    PolicyVersionNotFoundException,
)
from vulkan_engine.loaders import PolicyLoader, PolicyVersionLoader
from vulkan_engine.services.base import BaseService
from vulkan_engine.services.workflow import WorkflowService
from vulkan_engine.utils import validate_date_range
from vulkan_engine.validators import validate_uuid, validate_optional_uuid


class PolicyVersionService(BaseService):
    """Service for managing policy versions and their operations."""

    def __init__(
        self,
        db: Session,
        workflow_service: WorkflowService,
        launcher: DagsterRunLauncher | None = None,
        logger=None,
    ):
        """
        Initialize policy version service.

        Args:
            db: Database session
            dagster_service_client: Dagster service client
            launcher: Dagster run launcher
            logger: Optional logger
        """
        super().__init__(db, logger)
        self.launcher = launcher
        self.workflow_service = workflow_service
        self.policy_loader = PolicyLoader(db)
        self.policy_version_loader = PolicyVersionLoader(db)

    def create_policy_version(
        self, config: schemas.PolicyVersionCreate, project_id: str = None
    ) -> schemas.PolicyVersion:
        """
        Create a new policy version.

        Args:
            config: Policy version creation data
            project_id: Optional project UUID to associate with

        Returns:
            Created PolicyVersion object

        Raises:
            PolicyNotFoundException: If policy doesn't exist
        """
        policy = self.policy_loader.get_policy(config.policy_id, project_id=project_id)

        # Create workflow for the policy version
        workflow = self.workflow_service.create_workflow(
            spec={"nodes": [], "input_schema": {}},
            requirements=[],
            variables=[],
            ui_metadata={},
            project_id=policy.project_id,
        )

        # Create version with initial INVALID status and link to workflow
        version = PolicyVersion(
            policy_id=config.policy_id,
            alias=config.alias,
            workflow_id=workflow.workflow_id,
            project_id=policy.project_id,
        )
        with self.db.begin():
            self.db.add(version)

        self._log_event(
            VulkanEvent.POLICY_VERSION_CREATED,
            policy_id=config.policy_id,
            policy_version_id=version.policy_version_id,
            policy_version_alias=config.alias,
        )

        return schemas.PolicyVersion.from_orm(version, workflow)

    def get_policy_version(
        self, policy_version_id: str, project_id: str = None
    ) -> PolicyVersion | None:
        """
        Get a policy version by ID, optionally filtered by project.

        Args:
            policy_version_id: Policy version UUID
            project_id: Optional project UUID to filter by

        Returns:
            PolicyVersion object or None if not found
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        try:
            return self.policy_version_loader.get_policy_version(
                policy_version_id, project_id=project_id
            )
        except PolicyVersionNotFoundException:
            return None

    def list_policy_versions(
        self,
        policy_id: str | None = None,
        archived: bool = False,
        project_id: str = None,
    ) -> list[PolicyVersion]:
        """
        List policy versions with optional filtering.

        Args:
            policy_id: Optional policy ID to filter by
            archived: Whether to include archived versions
            project_id: Optional project UUID to filter by

        Returns:
            List of PolicyVersion objects
        """
        return self.policy_version_loader.list_policy_versions(
            policy_id=policy_id, project_id=project_id, include_archived=archived
        )

    def update_policy_version(
        self,
        policy_version_id: str,
        config: schemas.PolicyVersionBase,
        project_id: str = None,
    ) -> PolicyVersion:
        """
        Update a policy version with new spec and configuration.

        Args:
            policy_version_id: Policy version UUID
            config: Update configuration
            project_id: Optional project UUID to filter by

        Returns:
            Updated PolicyVersion object

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist
            DSNotFound: If referenced data sources don't exist
            InvalidDataSourceException: If data source configuration is invalid
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        version = self.policy_version_loader.get_policy_version(
            policy_version_id, project_id=project_id, include_archived=False
        )

        self.logger.system.error(f"Got version {version}")
        # Update basic fields
        version.alias = config.alias

        workflow = self.workflow_service.update_workflow(
            workflow_id=version.workflow_id,
            spec=config.spec,
            requirements=config.requirements,
            variables=config.spec.config_variables or [],
            ui_metadata=config.ui_metadata,
            project_id=project_id,
        )
        self.logger.system.error(f"Updated workflow {version.workflow_id}")

        # Handle data source dependencies
        data_input_nodes = [
            node
            for node in config.spec.nodes
            if node.node_type == NodeType.DATA_INPUT.value
        ]
        # List of data source names used in the data input nodes
        used_data_sources = [node.metadata["data_source"] for node in data_input_nodes]

        if used_data_sources:
            data_sources = self._add_data_source_dependencies(
                version, used_data_sources
            )
            # For each data source, check if its required runtime params are
            # configured in the corresponding data-input-node "parameters" field.
            self._validate_data_source_runtime_params(data_input_nodes, data_sources)

        self.db.commit()
        self._log_event(
            VulkanEvent.POLICY_VERSION_UPDATED,
            policy_id=version.policy_id,
            policy_version_id=policy_version_id,
            policy_version_alias=version.alias,
        )

        return schemas.PolicyVersion.from_orm(version, workflow)

    def delete_policy_version(
        self, policy_version_id: str, project_id: str = None
    ) -> None:
        """
        Delete (archive) a policy version.

        Args:
            policy_version_id: Policy version UUID
            project_id: Optional project UUID to filter by

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist
            PolicyVersionInUseException: If version is in use by allocation strategy
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        try:
            version = self.policy_version_loader.get_policy_version(
                policy_version_id, project_id=project_id, include_archived=False
            )
        except PolicyVersionNotFoundException:
            raise PolicyVersionNotFoundException(
                f"Tried to delete non-existent policy version {policy_version_id}"
            )

        # Check if version is in use by allocation strategy
        self._check_version_not_in_use(version)

        # Delete the underlying workflow
        self.workflow_service.delete_workflow(version.workflow_id)

        version.archived = True
        self.db.commit()

        self._log_event(
            VulkanEvent.POLICY_VERSION_DELETED, policy_version_id=policy_version_id
        )

    def create_run(
        self,
        policy_version_id: str,
        input_data: dict,
        config_variables: dict,
        project_id: str = None,
    ) -> dict[str, str]:
        """
        Create a run for a policy version.

        Args:
            policy_version_id: Policy version UUID
            input_data: Input data for the run
            config_variables: Configuration variables
            project_id: Optional project UUID to associate with

        Returns:
            Dictionary with policy_version_id and run_id
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        if not self.launcher:
            raise Exception("No launcher available")

        run = self.launcher.create_run(
            input_data=input_data,
            policy_version_id=policy_version_id,
            run_config_variables=config_variables,
            project_id=project_id,
        )
        return {"policy_version_id": policy_version_id, "run_id": run.run_id}

    async def run_workflow(
        self,
        policy_version_id: str,
        input_data: dict,
        config_variables: dict,
        polling_interval_ms: int,
        polling_timeout_ms: int,
        project_id: str = None,
    ) -> schemas.RunResult:
        """
        Execute a workflow and wait for results.

        Args:
            policy_version_id: Policy version UUID
            input_data: Input data for the run
            config_variables: Configuration variables
            polling_interval_ms: Polling interval
            polling_timeout_ms: Polling timeout
            project_id: Optional project UUID to associate with

        Returns:
            RunResult object
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        if not self.launcher:
            raise Exception("No launcher available")

        run = self.launcher.create_run(
            input_data=input_data,
            policy_version_id=policy_version_id,
            run_config_variables=config_variables,
            project_id=project_id,
        )
        result = await get_run_result(
            self.db, run.run_id, polling_interval_ms, polling_timeout_ms
        )
        return result

    def list_configuration_variables(
        self, policy_version_id: str, project_id: str = None
    ) -> list[schemas.ConfigurationVariables]:
        """
        List configuration variables for a policy version.

        Args:
            policy_version_id: Policy version UUID
            project_id: Optional project UUID to filter by

        Returns:
            List of ConfigurationVariables

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        # Validate policy version exists
        version = self.policy_version_loader.get_policy_version(
            policy_version_id, project_id=project_id, include_archived=False
        )

        # Get variables from the workflow
        required_variables = version.workflow.variables or []

        variables = (
            self.db.query(ConfigurationValue)
            .filter_by(policy_version_id=policy_version_id)
            .all()
        )
        variable_map = {v.name: v for v in variables}

        result = []

        # Add existing variables
        for variable in variables:
            result.append(
                schemas.ConfigurationVariables(
                    name=variable.name,
                    value=variable.value,
                    created_at=variable.created_at,
                    last_updated_at=variable.last_updated_at,
                )
            )

        # Add missing required variables as null entries
        for variable in required_variables:
            if variable not in variable_map:
                result.append(
                    schemas.ConfigurationVariables(
                        name=variable,
                        value=None,
                        created_at=None,
                        last_updated_at=None,
                    )
                )

        return result

    def set_configuration_variables(
        self,
        policy_version_id: str,
        desired_variables: list[schemas.ConfigurationVariablesBase],
        project_id: str = None,
    ) -> dict[str, Any]:
        """
        Set configuration variables for a policy version.

        Args:
            policy_version_id: Policy version UUID
            desired_variables: List of variables to set
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with policy_version_id and variables

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        # Validate policy version exists
        self.policy_version_loader.get_policy_version(
            policy_version_id, project_id=project_id, include_archived=False
        )

        existing_variables = (
            self.db.query(ConfigurationValue)
            .filter_by(policy_version_id=policy_version_id)
            .all()
        )

        with self.db.begin():
            # Remove variables not in desired list
            desired_names = {var.name for var in desired_variables}
            for v in existing_variables:
                if v.name not in desired_names:
                    self.db.delete(v)

            # Update or create variables
            existing_map = {v.name: v for v in existing_variables}
            for v in desired_variables:
                config_value = existing_map.get(v.name)
                if not config_value:
                    config_value = ConfigurationValue(
                        policy_version_id=policy_version_id,
                        name=v.name,
                        value=v.value,
                    )
                    self.db.add(config_value)
                else:
                    config_value.value = v.value

        self._log_event(
            VulkanEvent.POLICY_VERSION_VARIABLES_UPDATED,
            policy_version_id=policy_version_id,
            variables=[v.model_dump_json() for v in desired_variables],
        )

        return {"policy_version_id": policy_version_id, "variables": desired_variables}

    def list_runs_by_policy_version(
        self,
        policy_version_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        project_id: str = None,
    ) -> list[Run]:
        """
        List runs for a policy version.

        Args:
            policy_version_id: Policy version UUID
            start_date: Start date filter
            end_date: End date filter
            project_id: Optional project UUID to filter by

        Returns:
            List of Run objects
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        start_date, end_date = validate_date_range(start_date, end_date)

        query = select(Run).filter(
            (Run.policy_version_id == policy_version_id)
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )

        if project_id is not None:
            query = query.filter(Run.project_id == project_id)

        query = query.order_by(Run.created_at.desc())

        return self.db.execute(query).scalars().all()

    def list_data_sources_by_policy_version(
        self, policy_version_id: str, project_id: str = None
    ) -> list[schemas.DataSourceReference]:
        """
        List data sources used by a policy version.

        Args:
            policy_version_id: Policy version UUID
            project_id: Optional project UUID to filter by

        Returns:
            List of DataSourceReference objects

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist
        """
        # Validate policy version ID
        validate_uuid(policy_version_id, "policy version")

        # Validate policy version exists
        version = self.policy_version_loader.get_policy_version(
            policy_version_id, project_id=project_id
        )

        dependencies = (
            self.db.query(WorkflowDataDependency)
            .filter_by(workflow_id=version.workflow_id)
            .all()
        )

        result = []
        for dep in dependencies:
            ds = (
                self.db.query(DataSource)
                .filter_by(data_source_id=dep.data_source_id)
                .first()
            )
            if ds:
                result.append(
                    schemas.DataSourceReference(
                        data_source_id=ds.data_source_id,
                        name=ds.name,
                        created_at=ds.created_at,
                    )
                )

        return result

    def _add_data_source_dependencies(
        self, version: PolicyVersion, data_sources: list[str]
    ) -> dict[str, DataSource]:
        """Add data source dependencies for a policy version."""
        query = select(DataSource).where(
            DataSource.name.in_(data_sources),
            DataSource.archived.is_(False),
        )
        matched = self.db.execute(query).scalars().all()

        missing = set(data_sources) - {m.name for m in matched}
        if missing:
            raise DataSourceNotFoundException(
                f"The following data sources are not defined: {list(missing)}"
            )

        for ds in matched:
            dependency = WorkflowDataDependency(
                data_source_id=ds.data_source_id,
                workflow_id=version.workflow_id,
            )
            self.db.add(dependency)

        return {str(ds.name): ds for ds in matched}

    def _validate_data_source_runtime_params(
        self, data_input_nodes: list, data_sources: dict[str, DataSource]
    ) -> None:
        """Validate data source runtime parameters."""
        for node in data_input_nodes:
            ds = data_sources[node.metadata["data_source"]]
            if ds.runtime_params:
                configured_params = set(node.metadata["parameters"].keys())
                required_params = set(ds.runtime_params)
                if required_params != configured_params:
                    raise InvalidDataSourceException(
                        f"Data source {ds.name} requires runtime parameters "
                        f"{list(required_params)} but got {list(configured_params)} "
                        f"from {node.name}"
                    )

    def _check_version_not_in_use(self, version: PolicyVersion) -> None:
        """Check if policy version is in use by allocation strategy."""
        policy = self.db.query(Policy).filter_by(policy_id=version.policy_id).first()
        if policy and policy.allocation_strategy:
            strategy = schemas.PolicyAllocationStrategy.model_validate(
                policy.allocation_strategy
            )
            active_versions = [opt.policy_version_id for opt in strategy.choice]
            if strategy.shadow:
                active_versions.extend(strategy.shadow)

            if str(version.policy_version_id) in active_versions:
                raise PolicyVersionInUseException(
                    f"Policy version {version.policy_version_id} is currently in use by the policy "
                    f"allocation strategy for policy {policy.policy_id}"
                )
