import enum
import os

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
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


class Role(enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Project(Base):
    __tablename__ = "project"

    project_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectUser(Base):
    __tablename__ = "project_user"

    project_user_id = Column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    project_id = Column(Uuid, ForeignKey("project.project_id"))
    user_id = Column(Uuid, ForeignKey("users.user_id"))
    role = Column(Enum(Role))


class User(Base):
    __tablename__ = "users"

    user_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    user_auth_id = Column(String, unique=True)
    email = Column(String, unique=True)
    name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Policy(Base):
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Access Control
    project_id = Column(Uuid, ForeignKey("project.project_id"))


class Component(Base):
    __tablename__ = "component"

    component_id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String)
    project_id = Column(Uuid, ForeignKey("project.project_id"))


class ComponentVersion(Base):
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
    project_id = Column(Uuid, ForeignKey("project.project_id"))


class PolicyVersion(Base):
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Access Control
    project_id = Column(Uuid, ForeignKey("project.project_id"))


class ComponentVersionDependency(Base):
    __tablename__ = "component_version_dependency"

    component_version_dependency_id = Column(
        Integer, primary_key=True, autoincrement=True
    )
    policy_version_id = Column(Uuid, ForeignKey("policy_version.policy_version_id"))
    component_version_id = Column(
        Uuid, ForeignKey("component_version.component_version_id")
    )


class DagsterWorkspace(Base):
    __tablename__ = "dagster_workspace"

    policy_version_id = Column(
        Uuid,
        ForeignKey("policy_version.policy_version_id"),
        primary_key=True,
    )
    status = Column(Enum(DagsterWorkspaceStatus))
    path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Run(Base):
    __tablename__ = "run"

    run_id = Column(Integer, primary_key=True, autoincrement=True)
    policy_version_id = Column(Uuid, ForeignKey("policy.policy_id"))
    status = Column(Enum(RunStatus))
    result = Column(String, nullable=True)
    dagster_run_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class StepMetadata(Base):
    __tablename__ = "step_metadata"

    step_metadata_id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    run_id = Column(Integer, ForeignKey("run.run_id"))
    step_name = Column(String)
    node_type = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    error = Column(String, nullable=True)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
