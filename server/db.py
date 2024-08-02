import enum

from sqlalchemy import (
    ARRAY,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()
engine = create_engine("sqlite:///server/example.db", echo=True)
DBSession = sessionmaker(bind=engine)

class PolicyVersionStatus(enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class DagsterWorkspaceStatus(enum.Enum):
    OK = "OK"
    CREATION_PENDING = "CREATION_PENDING"
    CREATION_FAILED = "CREATION_FAILED"


class Policy(Base):

    __tablename__ = "policy"

    policy_id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    input_schema = Column(String, nullable=True)
    output_schema = Column(String, nullable=True)
    # We might want to have a split between versions.
    # I don't know a good way to do that yet.
    active_policy_version_id = Column(
        Integer,
        ForeignKey("policy_version.policy_version_id"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Component(Base):

    __tablename__ = "component"

    component_id = Column(Integer, primary_key=True)
    name = Column(String)


class ComponentVersion(Base):

    __tablename__ = "component_version"

    component_version_id = Column(Integer, primary_key=True)
    component_id = Column(Integer, ForeignKey("component.component_id"))
    alias = Column(String)
    input_schema = Column(String)
    output_schema = Column(String)
    repository = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PolicyVersion(Base):

    __tablename__ = "policy_version"

    policy_version_id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("policy.policy_id"))
    alias = Column(String)
    status = Column(Enum(PolicyVersionStatus))
    repository = Column(String)
    repository_version = Column(String)
    # TODO: SQLite doesn't support ARRAY type. Change this when moving to Postgres.
    component_version_ids = Column(String, nullable=True)
    entrypoint = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DagsterWorkspace(Base):

    __tablename__ = "dagster_workspace"

    policy_version_id = Column(
        Integer, ForeignKey("policy_version.policy_version_id"), primary_key=True
    )
    status = Column(Enum(DagsterWorkspaceStatus))
    path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Run(Base):

    __tablename__ = "run"

    run_id = Column(Integer, primary_key=True)
    policy_version_id = Column(Integer, ForeignKey("policy.policy_id"))
    status = Column(String)
    result = Column(String, nullable=True)
    dagster_run_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StepMetadata(Base):

    __tablename__ = "step_metadata"

    step_metadata_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    run_id = Column(Integer, ForeignKey("run.run_id"))
    step_name = Column(String)
    node_type = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    error = Column(String, nullable=True)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
