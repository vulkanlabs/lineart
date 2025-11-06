import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from vulkan_engine import schemas
from vulkan_engine.schemas import RunStatus
from vulkan_server.app import app
from vulkan_server.dependencies import get_policy_service


@pytest.fixture
def mock_policy_service():
    """Create a mock PolicyService."""
    return MagicMock()


@pytest.fixture
def client(mock_policy_service):
    """Create a test client with mocked dependencies."""

    def override_get_policy_service():
        return mock_policy_service

    app.dependency_overrides[get_policy_service] = override_get_policy_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


class TestListRunsByPolicy:
    """Test cases for list_runs_by_policy endpoint."""

    def test_list_runs_by_policy_with_datetime_query_params(
        self, client, mock_policy_service
    ):
        """Test that datetime query params are converted to date objects."""
        # Setup
        policy_id = "test-policy-id"
        start_datetime = datetime.datetime(2025, 1, 15, 10, 30, 45)
        end_datetime = datetime.datetime(2025, 1, 20, 14, 22, 33)

        now = datetime.datetime.now(datetime.timezone.utc)
        mock_runs = [
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.SUCCESS,
                created_at=now,
                last_updated_at=now,
            ),
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.PENDING,
                created_at=now,
                last_updated_at=now,
            ),
        ]
        mock_policy_service.list_runs_by_policy.return_value = mock_runs

        # Execute
        response = client.get(
            f"/policies/{policy_id}/runs",
            params={
                "start_date": start_datetime.isoformat(),
                "end_date": end_datetime.isoformat(),
            },
        )

        # Assert
        assert response.status_code == 200
        mock_policy_service.list_runs_by_policy.assert_called_once()
        call_args = mock_policy_service.list_runs_by_policy.call_args

        assert call_args[0][0] == policy_id
        assert call_args[0][1] == start_datetime.date()
        assert call_args[0][2] == end_datetime.date()

    def test_list_runs_by_policy_with_date_only_params(
        self, client, mock_policy_service
    ):
        """Test that date-only strings are accepted and converted correctly."""
        # Setup
        policy_id = "test-policy-id"
        start_date_str = "2025-01-15"
        end_date_str = "2025-01-20"

        now = datetime.datetime.now(datetime.timezone.utc)
        mock_runs = [
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.SUCCESS,
                created_at=now,
                last_updated_at=now,
            )
        ]
        mock_policy_service.list_runs_by_policy.return_value = mock_runs

        # Execute
        response = client.get(
            f"/policies/{policy_id}/runs",
            params={
                "start_date": start_date_str,
                "end_date": end_date_str,
            },
        )

        # Assert
        assert response.status_code == 200
        mock_policy_service.list_runs_by_policy.assert_called_once()
        call_args = mock_policy_service.list_runs_by_policy.call_args

        assert call_args[0][1] == datetime.date(2025, 1, 15)
        assert call_args[0][2] == datetime.date(2025, 1, 20)

    def test_list_runs_by_policy_without_date_params(self, client, mock_policy_service):
        """Test that None dates are passed through correctly."""
        # Setup
        policy_id = "test-policy-id"
        now = datetime.datetime.now(datetime.timezone.utc)
        mock_runs = [
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.SUCCESS,
                created_at=now,
                last_updated_at=now,
            )
        ]
        mock_policy_service.list_runs_by_policy.return_value = mock_runs

        # Execute
        response = client.get(f"/policies/{policy_id}/runs")

        # Assert
        assert response.status_code == 200
        mock_policy_service.list_runs_by_policy.assert_called_once()
        call_args = mock_policy_service.list_runs_by_policy.call_args

        assert call_args[0][0] == policy_id
        assert call_args[0][1] is None
        assert call_args[0][2] is None

    def test_list_runs_by_policy_with_only_start_date(
        self, client, mock_policy_service
    ):
        """Test with only start_date provided."""
        # Setup
        policy_id = "test-policy-id"
        start_datetime = datetime.datetime(2025, 1, 15, 10, 30, 45)

        now = datetime.datetime.now(datetime.timezone.utc)
        mock_runs = [
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.SUCCESS,
                created_at=now,
                last_updated_at=now,
            )
        ]
        mock_policy_service.list_runs_by_policy.return_value = mock_runs

        # Execute
        response = client.get(
            f"/policies/{policy_id}/runs",
            params={"start_date": start_datetime.isoformat()},
        )

        # Assert
        assert response.status_code == 200
        mock_policy_service.list_runs_by_policy.assert_called_once()
        call_args = mock_policy_service.list_runs_by_policy.call_args

        assert call_args[0][1] == start_datetime.date()
        assert call_args[0][2] is None

    def test_list_runs_by_policy_with_only_end_date(self, client, mock_policy_service):
        """Test with only end_date provided."""
        # Setup
        policy_id = "test-policy-id"
        end_datetime = datetime.datetime(2025, 1, 20, 14, 22, 33)

        now = datetime.datetime.now(datetime.timezone.utc)
        mock_runs = [
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.SUCCESS,
                created_at=now,
                last_updated_at=now,
            )
        ]
        mock_policy_service.list_runs_by_policy.return_value = mock_runs

        # Execute
        response = client.get(
            f"/policies/{policy_id}/runs",
            params={"end_date": end_datetime.isoformat()},
        )

        # Assert
        assert response.status_code == 200
        mock_policy_service.list_runs_by_policy.assert_called_once()
        call_args = mock_policy_service.list_runs_by_policy.call_args

        assert call_args[0][1] is None
        assert call_args[0][2] == end_datetime.date()

    def test_list_runs_by_policy_returns_204_when_empty(
        self, client, mock_policy_service
    ):
        """Test that 204 is returned when no runs are found."""
        # Setup
        policy_id = "test-policy-id"
        mock_policy_service.list_runs_by_policy.return_value = []

        # Execute
        response = client.get(f"/policies/{policy_id}/runs")

        # Assert
        assert response.status_code == 204
        mock_policy_service.list_runs_by_policy.assert_called_once()

    def test_list_runs_by_policy_returns_runs_when_found(
        self, client, mock_policy_service
    ):
        """Test that runs are returned when found."""
        # Setup
        policy_id = "test-policy-id"
        now = datetime.datetime.now(datetime.timezone.utc)
        mock_runs = [
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.SUCCESS,
                created_at=now,
                last_updated_at=now,
            ),
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.PENDING,
                created_at=now,
                last_updated_at=now,
            ),
        ]
        mock_policy_service.list_runs_by_policy.return_value = mock_runs

        # Execute
        response = client.get(f"/policies/{policy_id}/runs")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["status"] == "SUCCESS"
        assert data[1]["status"] == "PENDING"
        mock_policy_service.list_runs_by_policy.assert_called_once()

    def test_list_runs_by_policy_converts_timezone_aware_datetime(
        self, client, mock_policy_service
    ):
        """Test that timezone-aware datetime strings are handled correctly."""
        # Setup
        policy_id = "test-policy-id"
        start_datetime_str = "2025-01-15T10:30:45.123456+00:00"
        end_datetime_str = "2025-01-20T14:22:33.654321-05:00"

        now = datetime.datetime.now(datetime.timezone.utc)
        mock_runs = [
            schemas.Run(
                run_id=uuid4(),
                policy_version_id=uuid4(),
                status=RunStatus.SUCCESS,
                created_at=now,
                last_updated_at=now,
            )
        ]
        mock_policy_service.list_runs_by_policy.return_value = mock_runs

        # Execute
        response = client.get(
            f"/policies/{policy_id}/runs",
            params={
                "start_date": start_datetime_str,
                "end_date": end_datetime_str,
            },
        )

        # Assert
        assert response.status_code == 200
        mock_policy_service.list_runs_by_policy.assert_called_once()
        call_args = mock_policy_service.list_runs_by_policy.call_args

        assert call_args[0][1] == datetime.date(2025, 1, 15)
        assert call_args[0][2] == datetime.date(2025, 1, 20)
