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
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from vulkan.core.run import RunStatus, WorkflowStatus
from vulkan.credentials import CredentialType
from vulkan.data_source import DataSourceStatus
from vulkan.schemas import CachingOptions, DataSourceSpec
from vulkan.spec.nodes.base import NodeType

from vulkan_engine.config import DatabaseConfig
from vulkan_engine.schemas import DataObjectOrigin

Base = declarative_base()


def create_engine_from_config(database_config: DatabaseConfig) -> Engine:
    """Create database engine from configuration."""
    return create_engine(database_config.connection_string, echo=False)


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
    workflow_id = Column(Uuid, ForeignKey("workflow.workflow_id"))
    alias = Column(String, nullable=True)
    project_id = Column(Uuid, nullable=True)
    workflow = relationship("Workflow", backref="policy_versions")

    __table_args__ = (Index("idx_policy_version_project_id", "project_id"),)


class Workflow(TimedUpdateMixin, Base):
    __tablename__ = "workflow"

    workflow_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    spec = Column(JSON, nullable=False)
    requirements = Column(ARRAY(String), nullable=False)
    variables = Column(ARRAY(String), nullable=False)

    # Metadata related to workflow backend and UI states.
    status = Column(Enum(WorkflowStatus), nullable=False)
    ui_metadata = Column(JSON, nullable=False)

    project_id = Column(Uuid, nullable=True)

    __table_args__ = (Index("idx_workflow_project_id", "project_id"),)


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
    input_data = Column(JSON, nullable=True)
    # Attribute name 'metadata' is reserved when using the Declarative API.
    run_metadata = Column(JSON, nullable=True)
    backend_run_id = Column(String, nullable=True)
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
    status = Column(Enum(DataSourceStatus), nullable=False, server_default="DRAFT")

    # Project association for multi-tenant deployments
    project_id = Column(Uuid, nullable=True)

    __table_args__ = (
        # Unique constraint for active data sources only (DRAFT + PUBLISHED)
        # Allows reusing names after archival
        Index(
            "unique_data_source_name",
            "name",
            unique=True,
            postgresql_where=(status != DataSourceStatus.ARCHIVED),
        ),
        Index("idx_data_source_status", "status"),
        Index("idx_data_source_project_status", "project_id", "status"),
    )

    @staticmethod
    def _extract_spec_values(spec: DataSourceSpec) -> dict:
        """Extract all field values from a spec into a dictionary."""
        variables = spec.extract_env_vars()
        runtime_params = spec.extract_runtime_params()

        return {
            "name": spec.name,
            "description": spec.description,
            "source": spec.source.model_dump(),
            "caching_enabled": spec.caching.enabled,
            "caching_ttl": spec.caching.calculate_ttl(),
            "config_metadata": spec.metadata,
            "runtime_params": runtime_params,
            "variables": variables,
        }

    @classmethod
    def from_spec(cls, spec: DataSourceSpec):
        """Create a new DataSource instance from a spec."""
        return cls(**cls._extract_spec_values(spec))

    def update_from_spec(self, spec: DataSourceSpec):
        """Update this data source instance from a spec (in-place)."""
        for key, value in self._extract_spec_values(spec).items():
            setattr(self, key, value)

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

    def is_published(self) -> bool:
        """Check if data source is published."""
        return self.status == DataSourceStatus.PUBLISHED


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


class DataSourceCredential(TimedUpdateMixin, Base):
    __tablename__ = "data_source_credential"

    credential_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    data_source_id = Column(
        Uuid, ForeignKey("data_source.data_source_id", ondelete="CASCADE")
    )

    credential_type = Column(Enum(CredentialType), nullable=False)
    value = Column(String, nullable=False)

    __table_args__ = (
        Index(
            "unique_data_source_credential_type",
            "data_source_id",
            "credential_type",
            unique=True,
        ),
    )


class WorkflowDataDependency(Base):
    __tablename__ = "workflow_data_dependency"

    id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    data_source_id = Column(Uuid, ForeignKey("data_source.data_source_id"))
    workflow_id = Column(Uuid, ForeignKey("workflow.workflow_id"))


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
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    error = Column(JSON, nullable=True)


class DataSourceTestResult(Base):
    __tablename__ = "data_source_test_result"

    test_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    request = Column(JSON, nullable=False)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Component(TimedUpdateMixin, ArchivableMixin, Base):
    __tablename__ = "component"

    component_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)  # Store base64 encoded image
    workflow_id = Column(Uuid, ForeignKey("workflow.workflow_id"))
    project_id = Column(Uuid, nullable=True)

    workflow = relationship("Workflow", backref="components")

    @declared_attr
    def __table_args__(cls):
        return (
            Index(
                "unique_component_name",
                "name",
                "archived",
                unique=True,
                postgresql_where=(cls.archived == False),  # noqa: E712
            ),
            Index("idx_component_project_id", "project_id"),
        )
