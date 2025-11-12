import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# Import the Base from vulkan_engine.db to get access to all models
from vulkan_engine.db import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Database URL is set programmatically by vulkan_engine.migrations module
# when running migrations via the Python API. For development scenarios
# (e.g., generating migrations via alembic CLI), fall back to environment variables.
if config.get_main_option("sqlalchemy.url") is None:
    # Fallback for development: construct URL from environment variables
    # These values should be set to point to your development database.
    db_user = os.getenv("DB_USER", "postgres_app_user")
    db_password = os.getenv("DB_PASSWORD", "postgres_app_password")
    db_database = os.getenv("DB_DATABASE", "postgres_app_db")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5433")

    if all([db_user, db_password, db_host, db_port, db_database]):
        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
        config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError(
            "Database URL not configured. Please set the following environment variables:\n"
            "  DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE"
        )

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
