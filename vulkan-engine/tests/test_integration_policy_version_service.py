from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.schemas import (
    PolicyCreate,
    PolicyVersionBase,
    PolicyVersionUpdate,
    WorkflowBase,
)
from vulkan_engine.services.policy import PolicyService
from vulkan_engine.services.policy_version import PolicyVersionService
from vulkan_engine.services.run_orchestration import RunOrchestrationService
from vulkan_engine.services.workflow import WorkflowService


@pytest.mark.asyncio
@pytest.mark.integration
class TestPolicyVersionServiceIntegration:
    """Integration tests for PolicyVersionService."""

    @pytest.fixture
    def policy_service(self, db_session: AsyncSession) -> PolicyService:
        return PolicyService(db_session)

    @pytest.fixture
    def workflow_service(self, db_session: AsyncSession) -> WorkflowService:
        return WorkflowService(db_session)

    @pytest.fixture
    def mock_backend(self):
        backend = MagicMock(spec=ExecutionBackend)
        backend.trigger_job.return_value = "mock-backend-run-id"
        return backend

    @pytest.fixture
    def run_orchestration_service(
        self, db_session: AsyncSession, mock_backend
    ) -> RunOrchestrationService:
        return RunOrchestrationService(db_session, mock_backend)

    @pytest.fixture
    def policy_version_service(
        self,
        db_session: AsyncSession,
        workflow_service: WorkflowService,
        run_orchestration_service: RunOrchestrationService,
    ) -> PolicyVersionService:
        return PolicyVersionService(
            db_session, workflow_service, run_orchestration_service
        )

    async def _create_sample_policy(
        self, policy_service: PolicyService, sample_project_id: str
    ) -> str:
        """Create a sample policy for testing and return its ID."""
        policy_data = PolicyCreate(
            name="test_policy",
            description="Test policy",
        )
        policy = await policy_service.create_policy(
            policy_data, project_id=sample_project_id
        )
        return policy.policy_id

    async def test_create_policy_version(
        self,
        policy_version_service: PolicyVersionService,
        policy_service: PolicyService,
        sample_project_id: str,
    ):
        """Test creating a new policy version."""
        sample_policy = await self._create_sample_policy(
            policy_service, sample_project_id
        )

        version_data = PolicyVersionBase(
            policy_id=sample_policy,
            alias="v1.0",
        )
        version = await policy_version_service.create_policy_version(
            version_data, project_id=sample_project_id
        )

        assert version.policy_version_id is not None
        assert version.policy_id == sample_policy
        assert version.alias == "v1.0"
        assert version.workflow is not None

    async def test_get_policy_version(
        self,
        policy_version_service: PolicyVersionService,
        policy_service: PolicyService,
        sample_project_id: str,
    ):
        """Test retrieving a policy version by ID."""
        sample_policy = await self._create_sample_policy(
            policy_service, sample_project_id
        )

        version_data = PolicyVersionBase(
            policy_id=sample_policy,
            alias="v1.0",
        )
        created_version = await policy_version_service.create_policy_version(
            version_data, project_id=sample_project_id
        )

        retrieved_version = await policy_version_service.get_policy_version(
            created_version.policy_version_id, project_id=sample_project_id
        )

        assert retrieved_version.policy_version_id == created_version.policy_version_id
        assert retrieved_version.alias == "v1.0"

    async def test_get_policy_version_not_found(
        self, policy_version_service: PolicyVersionService, sample_project_id: str
    ):
        """Test retrieving a non-existent policy version returns None."""
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        result = await policy_version_service.get_policy_version(
            non_existent_id, project_id=sample_project_id
        )
        assert result is None

    async def test_update_policy_version(
        self,
        policy_version_service: PolicyVersionService,
        policy_service: PolicyService,
        sample_project_id: str,
    ):
        """Test updating a policy version."""
        sample_policy = await self._create_sample_policy(
            policy_service, sample_project_id
        )

        version_data = PolicyVersionBase(
            policy_id=sample_policy,
            alias="v1.0",
        )
        created_version = await policy_version_service.create_policy_version(
            version_data, project_id=sample_project_id
        )

        update_data = PolicyVersionUpdate(
            alias="v1.1",
            workflow=WorkflowBase(
                spec={"nodes": [], "input_schema": {"cpf": "str", "name": "str"}},
                requirements=[],
            ),
        )
        updated_version = await policy_version_service.update_policy_version(
            created_version.policy_version_id, update_data, project_id=sample_project_id
        )

        assert updated_version.alias == "v1.1"
        assert updated_version.workflow is not None
        assert updated_version.workflow.spec.input_schema is not None
        assert "name" in updated_version.workflow.spec.input_schema

    async def test_list_policy_versions(
        self,
        policy_version_service: PolicyVersionService,
        policy_service: PolicyService,
        sample_project_id: str,
    ):
        """Test listing policy versions."""
        sample_policy = await self._create_sample_policy(
            policy_service, sample_project_id
        )

        for i in range(3):
            version_data = PolicyVersionBase(
                policy_id=sample_policy,
                alias=f"v1.{i}",
            )
            await policy_version_service.create_policy_version(
                version_data, project_id=sample_project_id
            )

        versions = await policy_version_service.list_policy_versions(
            policy_id=sample_policy, archived=False, project_id=sample_project_id
        )

        assert len(versions) == 3
        assert all(v.alias.startswith("v1.") for v in versions)

    async def test_archive_policy_version(
        self,
        policy_version_service: PolicyVersionService,
        policy_service: PolicyService,
        sample_project_id: str,
    ):
        """Test archiving a policy version."""
        sample_policy = await self._create_sample_policy(
            policy_service, sample_project_id
        )

        version_data = PolicyVersionBase(
            policy_id=sample_policy,
            alias="v1.0",
        )
        created_version = await policy_version_service.create_policy_version(
            version_data, project_id=sample_project_id
        )
        assert created_version.archived is False

        await policy_version_service.delete_policy_version(
            created_version.policy_version_id, project_id=sample_project_id
        )

        archived_version = await policy_version_service.get_policy_version(
            created_version.policy_version_id, project_id=sample_project_id
        )
        assert archived_version is not None
        assert archived_version.archived is True

    async def test_delete_policy_version(
        self,
        policy_version_service: PolicyVersionService,
        policy_service: PolicyService,
        sample_project_id: str,
    ):
        """Test deleting a policy version."""
        sample_policy = await self._create_sample_policy(
            policy_service, sample_project_id
        )

        version_data = PolicyVersionBase(
            policy_id=sample_policy,
            alias="v1.0",
        )
        created_version = await policy_version_service.create_policy_version(
            version_data, project_id=sample_project_id
        )

        await policy_version_service.delete_policy_version(
            created_version.policy_version_id, project_id=sample_project_id
        )

        deleted_version = await policy_version_service.get_policy_version(
            created_version.policy_version_id, project_id=sample_project_id
        )
        assert deleted_version is not None
        assert deleted_version.archived is True
