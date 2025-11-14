import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from vulkan.data_source import DataSourceStatus, HTTPSource
from vulkan.schemas import CachingOptions, DataSourceSpec
from vulkan_engine.db import DataSource
from vulkan_engine.exceptions import DataSourceNotFoundException
from vulkan_engine.services.data_source import DataSourceService


@pytest.mark.asyncio
@pytest.mark.integration
class TestDataSourceServiceIntegration:
    """Integration tests for DataSourceService."""

    async def test_create_data_source(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test creating a new data source."""
        service = DataSourceService(db_session)

        data_source_spec = DataSourceSpec(
            name="test_data_source",
            source=HTTPSource(
                url="https://api.example.com/data",
                method="GET",
                timeout=30,
                response_type="JSON",
            ),
            caching={"enabled": False},
        )

        data_source = await service.create_data_source(
            data_source_spec, project_id=sample_project_id
        )

        assert data_source.data_source_id is not None
        assert data_source.name == "test_data_source"

    async def test_get_data_source(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test retrieving a data source by ID."""
        service = DataSourceService(db_session)

        data_source_spec = DataSourceSpec(
            name="test_data_source",
            source=HTTPSource(
                url="https://api.example.com/data",
                method="GET",
                timeout=30,
                response_type="JSON",
            ),
            caching={"enabled": False},
        )
        created_ds = await service.create_data_source(
            data_source_spec, project_id=sample_project_id
        )

        retrieved_ds = await service.get_data_source(
            created_ds.data_source_id, project_id=sample_project_id
        )

        assert retrieved_ds.data_source_id == created_ds.data_source_id
        assert retrieved_ds.name == "test_data_source"

    async def test_get_data_source_not_found(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test retrieving a non-existent data source raises exception."""
        service = DataSourceService(db_session)
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(DataSourceNotFoundException):
            await service.get_data_source(non_existent_id, project_id=sample_project_id)

    async def test_update_data_source(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test updating a data source."""
        service = DataSourceService(db_session)

        data_source_spec = DataSourceSpec(
            name="original_name",
            source=HTTPSource(
                url="https://api.example.com/data",
                method="GET",
                timeout=30,
                response_type="JSON",
            ),
            caching={"enabled": False},
        )
        created_ds = await service.create_data_source(
            data_source_spec, project_id=sample_project_id
        )

        update_spec = DataSourceSpec(
            name="updated_name",
            source=HTTPSource(
                url="https://api.example.com/data/v2",
                method="POST",
                timeout=60,
                response_type="JSON",
            ),
            caching=CachingOptions(enabled=True, ttl=3600),
        )
        updated_ds = await service.update_data_source(
            created_ds.data_source_id, update_spec, project_id=sample_project_id
        )

        assert updated_ds.name == "updated_name"
        assert updated_ds.source.url == "https://api.example.com/data/v2"
        assert updated_ds.source.method == "POST"

    async def test_list_data_sources(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test listing data sources."""
        service = DataSourceService(db_session)

        for i in range(3):
            data_source_spec = DataSourceSpec(
                name=f"data_source_{i}",
                source=HTTPSource(
                    url=f"https://api.example.com/data/{i}",
                    method="GET",
                    timeout=30,
                    response_type="JSON",
                ),
                caching={"enabled": False},
            )
            await service.create_data_source(
                data_source_spec, project_id=sample_project_id
            )

        data_sources = await service.list_data_sources(
            include_archived=False, project_id=sample_project_id
        )

        assert len(data_sources) == 3
        assert all(ds.name.startswith("data_source_") for ds in data_sources)

    async def test_archive_data_source(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test archiving a data source."""
        service = DataSourceService(db_session)

        data_source_spec = DataSourceSpec(
            name="to_archive",
            source=HTTPSource(
                url="https://api.example.com/data",
                method="GET",
                timeout=30,
                response_type="JSON",
            ),
            caching={"enabled": False},
        )
        created_ds = await service.create_data_source(
            data_source_spec, project_id=sample_project_id
        )

        stmt = select(DataSource).filter_by(data_source_id=created_ds.data_source_id)
        result = await db_session.execute(stmt)
        ds = result.scalar_one()
        ds.status = DataSourceStatus.PUBLISHED
        await db_session.commit()

        archived_result = await service.delete_data_source(
            created_ds.data_source_id, project_id=sample_project_id
        )

        assert archived_result is not None
        assert archived_result["data_source_id"] == created_ds.data_source_id

    async def test_delete_data_source(
        self, db_session: AsyncSession, sample_project_id: str
    ):
        """Test deleting a data source."""
        service = DataSourceService(db_session)

        data_source_spec = DataSourceSpec(
            name="to_delete",
            source=HTTPSource(
                url="https://api.example.com/data",
                method="GET",
                timeout=30,
                response_type="JSON",
            ),
            caching={"enabled": False},
        )
        created_ds = await service.create_data_source(
            data_source_spec, project_id=sample_project_id
        )

        await service.delete_data_source(
            created_ds.data_source_id, project_id=sample_project_id
        )

        with pytest.raises(DataSourceNotFoundException):
            await service.get_data_source(
                created_ds.data_source_id, project_id=sample_project_id
            )
