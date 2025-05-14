import enum
import os
from functools import lru_cache

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
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from vulkan.core.run import JobStatus, RunStatus
from vulkan.schemas import CachingOptions, DataSourceSpec
from vulkan.spec.nodes.base import NodeType

from vulkan_server.schemas import DataObjectOrigin

Base = declarative_base()


@lru_cache
def _make_engine():
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_DATABASE = os.getenv("DB_DATABASE")
    if (
        DB_USER is None
        or DB_PASSWORD is None
        or DB_HOST is None
        or DB_PORT is None
        or DB_DATABASE is None
    ):
        raise ValueError(
            "Please set the following environment variables: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_DATABASE"
        )

    connection_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
    engine = create_engine(connection_str, echo=True)
    return engine


def get_db():
    engine = _make_engine()
    DBSession = sessionmaker(bind=engine)
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


class PolicyVersionStatus(enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class WorkspaceStatus(enum.Enum):
    OK = "OK"
    CREATION_PENDING = "CREATION_PENDING"
    CREATION_FAILED = "CREATION_FAILED"


class Role(enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class TimedUpdateMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ArchivableMixin:
    archived = Column(Boolean, default=False)


class User(TimedUpdateMixin, Base):
    __tablename__ = "users"

    user_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    user_auth_id = Column(String, unique=True)
    email = Column(String, unique=True)
    name = Column(String)


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


class PolicyVersion(TimedUpdateMixin, ArchivableMixin, Base):
    __tablename__ = "policy_version"

    policy_version_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    policy_id = Column(Uuid, ForeignKey("policy.policy_id"))
    alias = Column(String)
    status = Column(Enum(PolicyVersionStatus))
    spec = Column(JSON, nullable=False)
    requirements = Column(ARRAY(String), nullable=False)
    # The fields below require the policy version to be resolved
    # first, hence the "nullable=True". With regards to the application,
    # `input_schema` and `graph_definition` are actually non-nullable.
    input_schema = Column(JSON, nullable=True)
    variables = Column(ARRAY(String), nullable=True)
    ui_metadata = Column(JSON, nullable=True)

    # Base worker image
    base_worker_image = Column(String, nullable=True)


class BeamWorkspace(TimedUpdateMixin, Base):
    __tablename__ = "beam_workspace"

    policy_version_id = Column(
        Uuid,
        ForeignKey("policy_version.policy_version_id"),
        primary_key=True,
    )
    status = Column(Enum(WorkspaceStatus))
    image = Column(String, nullable=True)


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
    error = Column(String, nullable=True)
    extra = Column(JSON, nullable=True)


class DataSource(TimedUpdateMixin, Base):
    __tablename__ = "data_source"

    data_source_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    name = Column(String)
    description = Column(String, nullable=True)
    keys = Column(ARRAY(String))
    source = Column(JSON, nullable=False)
    caching_enabled = Column(Boolean)
    caching_ttl = Column(Integer, nullable=True)
    # Attribute name 'metadata' is reserved when using the Declarative API.
    config_metadata = Column(JSON, nullable=True)
    variables = Column(ARRAY(String), nullable=True)
    archived = Column(Boolean, default=False)

    __table_args__ = (
        Index(
            "unique_data_source_name",
            "name",
            "archived",
            unique=True,
            postgresql_where=(archived == False),  # noqa: E712
        ),
    )

    @classmethod
    def from_spec(cls, spec: DataSourceSpec):
        variables = spec.extract_env_vars()
        return cls(
            name=spec.name,
            description=spec.description,
            keys=spec.keys,
            source=spec.source.model_dump(),
            caching_enabled=spec.caching.enabled,
            caching_ttl=spec.caching.calculate_ttl(),
            config_metadata=spec.metadata,
            variables=variables,
        )

    def to_spec(self) -> DataSourceSpec:
        return DataSourceSpec(
            name=self.name,
            keys=self.keys,
            source=self.source,
            caching=CachingOptions(
                enabled=self.caching_enabled,
                ttl=self.caching_ttl,
            ),
            description=self.description,
            metadata=self.config_metadata,
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


class Backfill(TimedUpdateMixin, Base):
    __tablename__ = "backfill"

    backfill_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    backtest_id = Column(Uuid, ForeignKey("backtest.backtest_id"))
    input_data_path = Column(String)
    status = Column(Enum(RunStatus))
    config_variables = Column(JSON, nullable=True)

    # Known after launch
    output_path = Column(String, nullable=True)
    gcp_project_id = Column(String, nullable=True)
    gcp_job_id = Column(String, nullable=True)


class Backtest(TimedUpdateMixin, Base):
    __tablename__ = "backtest"

    backtest_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    policy_version_id = Column(
        Uuid, ForeignKey("policy_version.policy_version_id"), nullable=False
    )
    input_file_id = Column(
        Uuid, ForeignKey("uploaded_file.uploaded_file_id"), nullable=False
    )
    environments = Column(JSON, nullable=True)
    status = Column(Enum(JobStatus), nullable=False)

    # Optional, metrics-related fields
    calculate_metrics = Column(Boolean, nullable=False, default=False)
    target_column = Column(String, nullable=True)
    time_column = Column(String, nullable=True)
    group_by_columns = Column(ARRAY(String), nullable=True)


class BacktestMetrics(TimedUpdateMixin, Base):
    __tablename__ = "backtest_metrics"

    backtest_metrics_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    backtest_id = Column(Uuid, ForeignKey("backtest.backtest_id"), nullable=False)
    status = Column(Enum(RunStatus), nullable=False)

    # Known after launch
    output_path = Column(String, nullable=True)
    gcp_project_id = Column(String, nullable=True)
    gcp_job_id = Column(String, nullable=True)

    # Known after execution
    metrics = Column(JSON, nullable=True)


if __name__ == "__main__":
    engine = _make_engine()
    Base.metadata.create_all(engine)
