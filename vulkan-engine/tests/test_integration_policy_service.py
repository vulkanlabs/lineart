from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.exceptions import PolicyHasVersionsException, PolicyNotFoundException
from vulkan_engine.schemas import PolicyBase, PolicyCreate, PolicyVersionBase
from vulkan_engine.services.policy import PolicyService
from vulkan_engine.services.policy_version import PolicyVersionService
from vulkan_engine.services.run_orchestration import RunOrchestrationService
from vulkan_engine.services.workflow import WorkflowService


@pytest.mark.asyncio
@pytest.mark.integration
class TestPolicyServiceIntegration:
    """Integration tests for PolicyService."""

    async def test_create_policy(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test creating a new policy."""
        service = PolicyService(db_session)

        policy_data = PolicyCreate(
            name="test_policy",
            description="Test policy description",
        )

        policy = await service.create_policy(policy_data, project_id=sample_project_id)

        assert policy.policy_id is not None
        assert policy.name == "test_policy"
        assert policy.description == "Test policy description"
        assert policy.project_id == sample_project_id
        assert policy.archived is False

    async def test_get_policy(self, db_session: AsyncSession, sample_project_id: str):
        """Test retrieving a policy by ID."""
        service = PolicyService(db_session)

        policy_data = PolicyCreate(
            name="test_policy",
            description="Test description",
        )
        created_policy = await service.create_policy(
            policy_data, project_id=sample_project_id
        )

        retrieved_policy = await service.get_policy(
            created_policy.policy_id, project_id=sample_project_id
        )

        assert retrieved_policy.policy_id == created_policy.policy_id
        assert retrieved_policy.name == "test_policy"
        assert retrieved_policy.description == "Test description"

    async def test_get_policy_not_found(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test retrieving a non-existent policy raises exception."""
        service = PolicyService(db_session)
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(PolicyNotFoundException):
            await service.get_policy(non_existent_id, project_id=sample_project_id)

    async def test_update_policy(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test updating a policy."""
        service = PolicyService(db_session)

        policy_data = PolicyCreate(
            name="original_name",
            description="Original description",
        )
        created_policy = await service.create_policy(
            policy_data, project_id=sample_project_id
        )

        update_data = PolicyBase(
            name="updated_name",
            description="Updated description",
            allocation_strategy=None,
        )
        updated_policy = await service.update_policy(
            created_policy.policy_id, update_data, project_id=sample_project_id
        )

        assert updated_policy.name == "updated_name"
        assert updated_policy.description == "Updated description"

    async def test_list_policies(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test listing policies."""
        service = PolicyService(db_session)

        for i in range(3):
            policy_data = PolicyCreate(
                name=f"policy_{i}",
                description=f"Policy {i}",
            )
            await service.create_policy(policy_data, project_id=sample_project_id)

        policies = await service.list_policies(
            include_archived=False, project_id=sample_project_id
        )

        assert len(policies) == 3
        assert all(p.name.startswith("policy_") for p in policies)

    async def test_list_policies_excludes_archived(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test that listing policies excludes archived ones by default."""
        service = PolicyService(db_session)

        normal_policy_data = PolicyCreate(
            name="normal_policy",
            description="Normal",
        )
        normal_policy = await service.create_policy(
            normal_policy_data, project_id=sample_project_id
        )

        archived_policy_data = PolicyCreate(
            name="archived_policy",
            description="Archived",
        )
        archived_policy = await service.create_policy(
            archived_policy_data, project_id=sample_project_id
        )
        await service.delete_policy(
            archived_policy.policy_id, project_id=sample_project_id
        )

        policies = await service.list_policies(
            include_archived=False, project_id=sample_project_id
        )

        assert len(policies) == 1
        assert policies[0].policy_id == normal_policy.policy_id

        all_policies = await service.list_policies(
            include_archived=True, project_id=sample_project_id
        )

        assert len(all_policies) == 2

    async def test_archive_policy(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test archiving a policy."""
        service = PolicyService(db_session)

        policy_data = PolicyCreate(
            name="to_archive",
            description="Will be archived",
        )
        created_policy = await service.create_policy(
            policy_data, project_id=sample_project_id
        )
        assert created_policy.archived is False

        await service.delete_policy(
            created_policy.policy_id, project_id=sample_project_id
        )

        policy = await service.get_policy(
            created_policy.policy_id, project_id=sample_project_id
        )
        assert policy.archived is True

    async def test_delete_policy_without_versions(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test deleting a policy without versions."""
        service = PolicyService(db_session)

        policy_data = PolicyCreate(
            name="to_delete",
            description="Will be deleted",
        )
        created_policy = await service.create_policy(
            policy_data, project_id=sample_project_id
        )

        await service.delete_policy(
            created_policy.policy_id, project_id=sample_project_id
        )

        policy = await service.get_policy(
            created_policy.policy_id, project_id=sample_project_id
        )
        assert policy.archived is True

    async def test_delete_policy_with_versions_raises_exception(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test that deleting a policy with versions raises exception."""
        service = PolicyService(db_session)

        policy_data = PolicyCreate(
            name="policy_with_versions",
            description="Has versions",
        )
        created_policy = await service.create_policy(
            policy_data, project_id=sample_project_id
        )

        workflow_service = WorkflowService(db_session)
        mock_backend = MagicMock(spec=ExecutionBackend)
        mock_backend.trigger_job.return_value = "mock-backend-run-id"
        run_orchestration_service = RunOrchestrationService(db_session, mock_backend)
        policy_version_service = PolicyVersionService(
            db_session, workflow_service, run_orchestration_service
        )

        version_data = PolicyVersionBase(
            policy_id=created_policy.policy_id,
            alias="v1.0",
        )
        await policy_version_service.create_policy_version(
            version_data, project_id=sample_project_id
        )

        with pytest.raises(PolicyHasVersionsException):
            await service.delete_policy(
                created_policy.policy_id, project_id=sample_project_id
            )
