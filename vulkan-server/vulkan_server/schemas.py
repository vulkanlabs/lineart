from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from vulkan.core.run import RunStatus
from vulkan_public.schemas import DataSourceCreate


class Project(BaseModel):
    project_id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    user_auth_id: UUID
    email: str
    name: str


class User(UserBase):
    user_id: UUID
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class ProjectUserCreate(BaseModel):
    user_id: UUID
    role: str


class ProjectUserBase(ProjectUserCreate):
    project_id: UUID


class ProjectUser(ProjectUserBase):
    project_user_id: UUID
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class PolicyBase(BaseModel):
    name: str
    description: str
    active_policy_version_id: UUID | None = None


class PolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active_policy_version_id: UUID | None = None


class Policy(PolicyBase):
    policy_id: UUID
    project_id: UUID
    archived: bool
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class ComponentBase(BaseModel):
    name: str


class Component(ComponentBase):
    component_id: UUID
    project_id: UUID
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComponentVersionCreate(BaseModel):
    version_name: str
    repository: str


class ComponentVersion(BaseModel):
    component_id: UUID
    component_version_id: UUID
    alias: str
    input_schema: str
    instance_params_schema: str
    node_definitions: str
    created_at: datetime
    output_schema: str | None = None
    project_id: UUID
    archived: bool

    class Config:
        from_attributes = True


class ComponentVersionDependencyExpanded(BaseModel):
    component_id: UUID
    component_name: str
    component_version_id: UUID
    component_version_alias: str
    policy_id: UUID
    policy_version_id: UUID
    policy_name: str
    policy_version_alias: str


class PolicyVersionBase(BaseModel):
    policy_id: UUID
    alias: str | None = None


class PolicyVersionCreate(PolicyVersionBase):
    repository: str
    repository_version: str


class PolicyVersion(PolicyVersionBase):
    policy_version_id: UUID
    input_schema: dict[str, str]
    graph_definition: str
    project_id: UUID
    archived: bool
    created_at: datetime
    last_updated_at: datetime
    variables: list[str] | None = None

    class Config:
        from_attributes = True


class ConfigurationVariablesBase(BaseModel):
    name: str
    value: str | None = None


class ConfigurationVariables(ConfigurationVariablesBase):
    created_at: datetime | None = None
    last_updated_at: datetime | None = None


class Run(BaseModel):
    run_id: UUID
    policy_version_id: UUID
    project_id: UUID
    status: str
    result: str | None = None
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class StepMetadataBase(BaseModel):
    step_name: str
    node_type: str
    start_time: float
    end_time: float
    error: str | None = None
    extra: dict | None = None


class StepMetadata(StepMetadataBase):
    step_metadata_id: UUID
    run_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class _StepDetails(BaseModel):
    output: Any | None
    metadata: StepMetadataBase | None


class RunData(BaseModel):
    run_id: UUID
    status: str
    last_updated_at: datetime
    steps: dict[str, _StepDetails]

    class Config:
        from_attributes = True


class UserLogDetails(BaseModel):
    log_type: str = "LOG"
    message: str
    level: str


class DagsterLogDetails(BaseModel):
    log_type: str
    message: str


class LogEntry(BaseModel):
    timestamp: datetime
    step_key: str | None
    source: str
    event: UserLogDetails | DagsterLogDetails


class RunLogs(BaseModel):
    run_id: UUID
    status: str
    last_updated_at: datetime
    logs: list[LogEntry]


class DataSource(DataSourceCreate):
    data_source_id: UUID
    project_id: UUID
    variables: list[str] | None
    archived: bool
    created_at: datetime
    last_updated_at: datetime


class DataSourceReference(BaseModel):
    data_source_id: UUID
    name: str
    created_at: datetime


class DataObjectMetadata(BaseModel):
    data_object_id: UUID
    data_source_id: UUID
    project_id: UUID
    key: str
    created_at: datetime


class DataObject(DataObjectMetadata):
    value: Any

    class Config:
        from_attributes = True


class DataObjectOrigin(Enum):
    REQUEST = "REQUEST"
    CACHE = "CACHE"


class DataBrokerRequest(BaseModel):
    data_source_name: str
    request_body: dict[str, Any]
    variables: dict[str, str | None]


class DataBrokerResponse(BaseModel):
    data_object_id: UUID
    origin: DataObjectOrigin
    key: str
    value: Any


class Backfill(BaseModel):
    backfill_id: UUID
    backtest_id: UUID
    status: RunStatus

    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class BackfillStatus(BaseModel):
    backfill_id: UUID
    status: str


class Backtest(BaseModel):
    backtest_id: UUID
    policy_version_id: UUID
    input_file_id: UUID
    environments: list[dict]
    status: RunStatus

    created_at: datetime
    last_updated_at: datetime


class UploadedFile(BaseModel):
    uploaded_file_id: UUID
    file_schema: str
    created_at: datetime

    class Config:
        from_attributes = True


class BeamWorkspace(BaseModel):
    policy_version_id: UUID
    status: str

    class Config:
        from_attributes = True
