import enum
import os

from sqlalchemy import (
    JSON,
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    LargeBinary,
    String,
    Integer,
    Index,
    Uuid,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from vulkan.core.run import RunStatus

Base = declarative_base()

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

connection_str = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
)
engine = create_engine(connection_str, echo=True)
DBSession = sessionmaker(bind=engine)


def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


class PolicyVersionStatus(enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class DagsterWorkspaceStatus(enum.Enum):
    OK = "OK"
    CREATION_PENDING = "CREATION_PENDING"
    CREATION_FAILED = "CREATION_FAILED"
    INSTALL_FAILED = "INSTALL_FAILED"


class Role(enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class TimedUpdateMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuthorizationMixin:
    project_id = Column(Uuid, ForeignKey("project.project_id"))


class ArchivableMixin:
    archived = Column(Boolean, default=False)


class Project(Base):
    __tablename__ = "project"

    project_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class User(TimedUpdateMixin, Base):
    __tablename__ = "users"

    user_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    user_auth_id = Column(String, unique=True)
    email = Column(String, unique=True)
    name = Column(String)


class ProjectUser(TimedUpdateMixin, AuthorizationMixin, Base):
    __tablename__ = "project_user"

    project_user_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id = Column(Uuid, ForeignKey("users.user_id"))
    role = Column(Enum(Role))


class Policy(TimedUpdateMixin, AuthorizationMixin, ArchivableMixin, Base):
    __tablename__ = "policy"

    policy_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String)
    description = Column(String)
    input_schema = Column(String, nullable=True)
    output_schema = Column(String, nullable=True)
    # We might want to have a split between versions.
    # I don't know a good way to do that yet.
    active_policy_version_id = Column(
        Uuid,
        ForeignKey("policy_version.policy_version_id"),
        nullable=True,
    )


class Component(AuthorizationMixin, Base):
    __tablename__ = "component"

    component_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "unique_component_name",
            "project_id",
            "name",
            "archived",
            unique=True,
            postgresql_where=(archived == False),  # noqa: E712
        ),
    )


class ComponentVersion(AuthorizationMixin, ArchivableMixin, Base):
    __tablename__ = "component_version"

    component_version_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    component_id = Column(Uuid, ForeignKey("component.component_id"))
    alias = Column(String)
    input_schema = Column(String)
    output_schema = Column(String, nullable=True)
    instance_params_schema = Column(String)
    node_definitions = Column(String)
    repository = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PolicyVersion(TimedUpdateMixin, AuthorizationMixin, ArchivableMixin, Base):
    __tablename__ = "policy_version"

    policy_version_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    policy_id = Column(Uuid, ForeignKey("policy.policy_id"))
    alias = Column(String)
    status = Column(Enum(PolicyVersionStatus))
    repository = Column(String)
    repository_version = Column(String)
    graph_definition = Column(String)


class ComponentVersionDependency(Base):
    __tablename__ = "component_version_dependency"

    component_version_dependency_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    policy_version_id = Column(Uuid, ForeignKey("policy_version.policy_version_id"))
    component_version_id = Column(
        Uuid, ForeignKey("component_version.component_version_id")
    )


class DagsterWorkspace(TimedUpdateMixin, Base):
    __tablename__ = "dagster_workspace"

    policy_version_id = Column(
        Uuid,
        ForeignKey("policy_version.policy_version_id"),
        primary_key=True,
    )
    status = Column(Enum(DagsterWorkspaceStatus))
    path = Column(String, nullable=True)


class Run(TimedUpdateMixin, AuthorizationMixin, Base):
    __tablename__ = "run"

    run_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    policy_version_id = Column(Uuid, ForeignKey("policy_version.policy_version_id"))
    status = Column(Enum(RunStatus))
    result = Column(String, nullable=True)
    dagster_run_id = Column(String, nullable=True)


class StepMetadata(Base):
    __tablename__ = "step_metadata"

    step_metadata_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    run_id = Column(Uuid, ForeignKey("run.run_id"))
    step_name = Column(String)
    node_type = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    error = Column(String, nullable=True)
    extra = Column(JSON, nullable=True)


class DataSource(TimedUpdateMixin, AuthorizationMixin, Base):
    __tablename__ = "data_source"

    data_source_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    name = Column(String, unique=True)
    description = Column(String, nullable=True)
    keys = Column(ARRAY(String))
    request_url = Column(String)
    request_method = Column(String)
    request_headers = Column(JSON, nullable=True)
    request_params = Column(JSON, nullable=True)
    request_timeout = Column(Float, nullable=True)
    caching_enabled = Column(Boolean)
    caching_ttl = Column(Integer, nullable=True)
    retry_max_retries = Column(Integer, nullable=True)
    retry_backoff_factor = Column(Float, nullable=True)
    retry_status_forcelist = Column(ARRAY(Integer), nullable=True)
    # Attribute name 'metadata' is reserved when using the Declarative API.
    config_metadata = Column(JSON, nullable=True)


class DataObject(AuthorizationMixin, Base):
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


if __name__ == "__main__":
    Base.metadata.create_all(engine)
