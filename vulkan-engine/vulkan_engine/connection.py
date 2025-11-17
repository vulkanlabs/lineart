from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from vulkan_engine.config import DatabaseConfig

_engines: dict[str, AsyncEngine] = {}
_sessionmakers: dict[str, async_sessionmaker[AsyncSession]] = {}


def get_engine(database_config: DatabaseConfig) -> AsyncEngine:
    """
    Get or create database engine with connection pooling (singleton per connection string).

    Engines are cached by connection string to enable connection pooling.
    Each unique database configuration gets its own engine and connection pool.
    Pool configuration is read from database_config.

    Args:
        database_config: Database configuration with pool settings

    Returns:
        Cached AsyncEngine instance with connection pooling
    """
    connection_string = database_config.connection_string

    if connection_string not in _engines:
        _engines[connection_string] = create_async_engine(
            connection_string,
            pool_pre_ping=database_config.pool_pre_ping,
            pool_size=database_config.pool_size,
            max_overflow=database_config.max_overflow,
            pool_recycle=database_config.pool_recycle,
            echo=database_config.echo,
        )

    return _engines[connection_string]


def get_sessionmaker(
    database_config: DatabaseConfig,
) -> async_sessionmaker[AsyncSession]:
    """
    Get or create sessionmaker for database configuration (singleton per connection string).

    Sessionmakers are cached by connection string and reuse the pooled engine.

    Args:
        database_config: Database configuration

    Returns:
        Cached async_sessionmaker instance
    """
    connection_string = database_config.connection_string

    if connection_string not in _sessionmakers:
        engine = get_engine(database_config)
        _sessionmakers[connection_string] = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _sessionmakers[connection_string]


async def get_db_session(
    database_config: DatabaseConfig,
) -> AsyncIterator[AsyncSession]:
    """
    Get database session from configuration with connection pooling.

    This function uses a cached engine and sessionmaker to enable efficient
    connection pooling. Connections are reused from the pool, significantly
    reducing overhead compared to creating new engines for each request.

    Args:
        database_config: Database configuration

    Yields:
        AsyncSession instance from the connection pool
    """
    sessionmaker = get_sessionmaker(database_config)
    async with sessionmaker() as session:
        yield session


async def close_db(connection_string: str | None = None) -> None:
    """
    Close database connections and cleanup resources.

    Args:
        connection_string: Optional specific connection string to close.
                          If None, closes all engines.
    """
    global _engines, _sessionmakers

    if connection_string:
        if connection_string in _engines:
            await _engines[connection_string].dispose()
            del _engines[connection_string]
        if connection_string in _sessionmakers:
            del _sessionmakers[connection_string]
    else:
        for engine in _engines.values():
            await engine.dispose()
        _engines.clear()
        _sessionmakers.clear()
