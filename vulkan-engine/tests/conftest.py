"""
Test configuration and fixtures for vulkan-engine integration tests.

Provides async database session fixtures using Testcontainers for PostgreSQL.
"""

from collections.abc import AsyncGenerator
from urllib.parse import urlparse
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.postgres import PostgresContainer
from vulkan_engine.config import DatabaseConfig
from vulkan_engine.db import Base


@pytest.fixture(scope="session")
def postgres_container():
    """Create a PostgreSQL container using Testcontainers.

    This fixture is session-scoped, so the container is created once
    and reused across all tests in the session.

    Yields:
        PostgresContainer instance
    """
    with PostgresContainer("postgres:16") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_config(postgres_container: PostgresContainer) -> DatabaseConfig:
    """Create DatabaseConfig from the PostgreSQL container.

    Args:
        postgres_container: The PostgreSQL container fixture

    Returns:
        DatabaseConfig configured for the test container
    """
    # Get connection URL from container
    connection_url = postgres_container.get_connection_url()

    # Parse the URL to extract components
    # Format: postgresql://user:password@host:port/database
    parsed = urlparse(connection_url)

    return DatabaseConfig(
        user=parsed.username or "test",
        password=parsed.password or "test",
        host=parsed.hostname or "localhost",
        port=str(parsed.port) if parsed.port else "5432",
        database=parsed.path.lstrip("/") if parsed.path else "test",
    )


@pytest_asyncio.fixture(scope="session")
async def _create_tables(db_config: DatabaseConfig):
    """Create database tables once per test session.

    This fixture runs once before all tests to set up the schema.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(db_config.connection_string, poolclass=None)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    db_config: DatabaseConfig, _create_tables
) -> AsyncGenerator[AsyncSession, None]:
    """Create a PostgreSQL database session for testing.

    Uses Testcontainers to spin up a real PostgreSQL instance in Docker.
    This provides a more accurate test environment that matches production.

    Each test gets a fresh transaction that is rolled back after the test,
    ensuring test isolation. Services can call commit() within tests, and
    all changes will be rolled back at the end.

    Args:
        db_config: Database configuration from the container fixture
        _create_tables: Fixture that ensures tables are created

    Yields:
        Database session connected to PostgreSQL
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(
        db_config.connection_string,
        poolclass=None,
        echo=False,
    )
    sessionmaker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    session = sessionmaker()
    transaction = await session.begin()

    # Override commit to prevent actual commits during tests
    original_commit = session.commit

    async def mock_commit():
        # Just flush instead of committing
        await session.flush()

    session.commit = mock_commit

    try:
        yield session
    finally:
        # Restore original commit
        session.commit = original_commit
        # Rollback transaction
        try:
            await transaction.rollback()
        except Exception:
            pass
        try:
            await session.close()
        except Exception:
            pass
        # Don't dispose engine in async context - let garbage collection handle it
        # This avoids event loop issues during test cleanup


@pytest.fixture
def sample_project_id() -> str:
    """Generate a sample project UUID for testing.

    Returns:
        Sample project UUID as string
    """
    return str(uuid4())


@pytest.fixture
def sample_policy_id() -> str:
    """Generate a sample policy UUID for testing.

    Returns:
        Sample policy UUID as string
    """
    return str(uuid4())


@pytest.fixture
def sample_policy_version_id() -> str:
    """Generate a sample policy version UUID for testing.

    Returns:
        Sample policy version UUID as string
    """
    return str(uuid4())


@pytest.fixture
def sample_data_source_id() -> str:
    """Generate a sample data source UUID for testing.

    Returns:
        Sample data source UUID as string
    """
    return str(uuid4())


@pytest.fixture
def sample_run_id() -> str:
    """Generate a sample run UUID for testing.

    Returns:
        Sample run UUID as string
    """
    return str(uuid4())
