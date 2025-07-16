from typing import Iterator

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Uuid,
    create_engine,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.sql import func

from vulkan.core.run import PolicyVersionStatus, RunStatus
from vulkan.schemas import CachingOptions, DataSourceSpec
from vulkan.spec.nodes.base import NodeType
from vulkan_engine.config import DatabaseConfig
from vulkan_engine.schemas import DataObjectOrigin

Base = declarative_base()


def create_engine_from_config(database_config: DatabaseConfig) -> Engine:
    """Create database engine from configuration."""
    return create_engine(database_config.connection_string, echo=True)


def get_db_session(database_config: DatabaseConfig) -> Iterator[Session]:
    """Get database session from configuration."""
    engine = create_engine_from_config(database_config)
    DBSession = sessionmaker(bind=engine)
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


class TimedUpdateMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ArchivableMixin:
    archived = Column(Boolean, default=False)


class LogRecord(Base):
    __tablename__ = "log_record"

    log_record_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    level = Column(String)
    message = Column(JSON)
    timestamp = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Policy(TimedUpdateMixin, ArchivableMixin, Base):
    __tablename__ = "policy"

    policy_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String)
    description = Column(String)
    allocation_strategy = Column(JSON, nullable=True)

    # Project association for multi-tenant deployments
    project_id = Column(Uuid, nullable=True)

    __table_args__ = (Index("idx_policy_project_id", "project_id"),)


class PolicyVersion(TimedUpdateMixin, ArchivableMixin, Base):
    __tablename__ = "policy_version"

    policy_version_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    policy_id = Column(Uuid, ForeignKey("policy.policy_id"))
    alias = Column(String, nullable=True)
    status = Column(Enum(PolicyVersionStatus), nullable=False)
    spec = Column(JSON, nullable=False)
    requirements = Column(ARRAY(String), nullable=False)
    variables = Column(ARRAY(String), nullable=True)
    ui_metadata = Column(JSON, nullable=True)

    # Project association for multi-tenant deployments (denormalized for performance)
    project_id = Column(Uuid, nullable=True)

    __table_args__ = (Index("idx_policy_version_project_id", "project_id"),)


class ConfigurationValue(TimedUpdateMixin, Base):
    __tablename__ = "configuration_value"

    configuration_value_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    policy_version_id = Column(Uuid, ForeignKey("policy_version.policy_version_id"))

    name = Column(String)
    value = Column(JSON, nullable=True)
    nullable = Column(Boolean)

    __table_args__ = (
        Index(
            "unique_policy_version_name",
            "policy_version_id",
            "name",
            unique=True,
        ),
        CheckConstraint(
            sqltext="value IS NOT NULL OR nullable = TRUE",
            name="value_null_only_if_allowed",
        ),
    )


class RunGroup(TimedUpdateMixin, Base):
    __tablename__ = "run_group"

    run_group_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    policy_id = Column(Uuid, ForeignKey("policy.policy_id"))
    input_data = Column(JSON)


class Run(TimedUpdateMixin, Base):
    __tablename__ = "run"

    run_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    run_group_id = Column(Uuid, ForeignKey("run_group.run_group_id"), nullable=True)
    policy_version_id = Column(Uuid, ForeignKey("policy_version.policy_version_id"))
    status = Column(Enum(RunStatus))
    result = Column(String, nullable=True)
    # Attribute name 'metadata' is reserved when using the Declarative API.
    run_metadata = Column(JSON, nullable=True)
    dagster_run_id = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)

    # Project association for multi-tenant deployments (denormalized for performance)
    project_id = Column(Uuid, nullable=True)

    __table_args__ = (Index("idx_run_project_id", "project_id"),)


class StepMetadata(Base):
    __tablename__ = "step_metadata"

    step_metadata_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    run_id = Column(Uuid, ForeignKey("run.run_id"))
    step_name = Column(String)
    node_type = Column(Enum(NodeType))
    start_time = Column(Float)
    end_time = Column(Float)
    error = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)


class DataSource(TimedUpdateMixin, Base):
    __tablename__ = "data_source"

    data_source_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    name = Column(String)
    description = Column(String, nullable=True)
    source = Column(JSON, nullable=False)
    caching_enabled = Column(Boolean)
    caching_ttl = Column(Integer, nullable=True)
    # Attribute name 'metadata' is reserved when using the Declarative API.
    config_metadata = Column(JSON, nullable=True)
    runtime_params = Column(ARRAY(String), nullable=True)
    variables = Column(ARRAY(String), nullable=True)
    archived = Column(Boolean, default=False)

    # Project association for multi-tenant deployments
    project_id = Column(Uuid, nullable=True)

    __table_args__ = (
        Index(
            "unique_data_source_name",
            "name",
            "archived",
            unique=True,
            postgresql_where=(archived == False),  # noqa: E712
        ),
        Index("idx_data_source_project_id", "project_id"),
    )

    @classmethod
    def from_spec(cls, spec: DataSourceSpec):
        variables = spec.extract_env_vars()
        runtime_params = spec.extract_runtime_params()

        return cls(
            name=spec.name,
            description=spec.description,
            source=spec.source.model_dump(),
            caching_enabled=spec.caching.enabled,
            caching_ttl=spec.caching.calculate_ttl(),
            config_metadata=spec.metadata,
            runtime_params=runtime_params,
            variables=variables,
        )

    def to_spec(self) -> DataSourceSpec:
        return DataSourceSpec(
            name=self.name,
            source=self.source,
            caching=CachingOptions(
                enabled=self.caching_enabled,
                ttl=self.caching_ttl,
            ),
            description=self.description,
            metadata=self.config_metadata,
        )


class DataSourceEnvVar(TimedUpdateMixin, Base):
    __tablename__ = "data_source_env_var"

    data_source_env_var_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    data_source_id = Column(Uuid, ForeignKey("data_source.data_source_id"))

    name = Column(String)
    value = Column(JSON, nullable=True)
    nullable = Column(Boolean)

    __table_args__ = (
        Index(
            "unique_data_source_env_var_name",
            "data_source_id",
            "name",
            unique=True,
        ),
        CheckConstraint(
            sqltext="value IS NOT NULL OR nullable = TRUE",
            name="value_null_only_if_allowed",
        ),
    )


class PolicyDataDependency(Base):
    __tablename__ = "policy_data_dependency"

    id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    data_source_id = Column(Uuid, ForeignKey("data_source.data_source_id"))
    policy_version_id = Column(Uuid, ForeignKey("policy_version.policy_version_id"))


class DataObject(Base):
    __tablename__ = "data_object"

    data_object_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    data_source_id = Column(Uuid, ForeignKey("data_source.data_source_id"))
    key = Column(String)
    value = Column(LargeBinary)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # TODO: forbid updates to this table


class RunDataCache(Base):
    __tablename__ = "run_data_cache"

    key = Column(String, primary_key=True)
    data_object_id = Column(Uuid, ForeignKey("data_object.data_object_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RunDataRequest(Base):
    __tablename__ = "run_data_request"

    run_data_request_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    run_id = Column(Uuid, ForeignKey("run.run_id"))
    data_object_id = Column(Uuid, ForeignKey("data_object.data_object_id"))
    data_source_id = Column(Uuid, ForeignKey("data_source.data_source_id"))
    data_origin = Column(Enum(DataObjectOrigin), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UploadedFile(Base):
    __tablename__ = "uploaded_file"

    uploaded_file_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    file_schema = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# To create tables, use create_engine_from_config with appropriate DatabaseConfig
