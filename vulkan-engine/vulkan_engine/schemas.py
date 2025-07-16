from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from vulkan.core.run import JobStatus, PolicyVersionStatus, RunStatus
from vulkan.schemas import DataSourceSpec, PolicyAllocationStrategy
from vulkan.spec.policy import PolicyDefinitionDict


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


class PolicyCreate(BaseModel):
    name: str
    description: str


class PolicyBase(BaseModel):
    name: str | None = None
    description: str | None = None
    allocation_strategy: PolicyAllocationStrategy | None = None


class Policy(PolicyBase):
    policy_id: UUID
    archived: bool
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class UINodePosition(BaseModel):
    x: float
    y: float


class UIMetadata(BaseModel):
    position: UINodePosition
    width: float
    height: float


class ComponentBase(BaseModel):
    name: str
    description: str | None = None
    icon: str | None = None  # Base64 encoded image
    requirements: list[str] | None = None
    spec: PolicyDefinitionDict | None = None
    input_schema: dict[str, str] | None = None
    variables: list[str] | None = None
    ui_metadata: dict[str, UIMetadata] | None = None


class Component(ComponentBase):
    component_id: UUID
    archived: bool
    created_at: datetime
    last_updated_at: datetime
    requirements: list[str]
    spec: PolicyDefinitionDict
    input_schema: dict[str, str]
    variables: list[str] | None = None
    ui_metadata: dict[str, UIMetadata] | None = None

    class Config:
        from_attributes = True


class PolicyVersionBase(BaseModel):
    alias: str | None
    spec: PolicyDefinitionDict
    input_schema: dict[str, str] | None = None
    requirements: list[str] | None = None
    ui_metadata: dict[str, UIMetadata] | None = None


class PolicyVersionCreate(BaseModel):
    policy_id: UUID
    alias: str | None


class PolicyVersion(BaseModel):
    policy_version_id: UUID
    policy_id: UUID
    alias: str | None = None
    status: PolicyVersionStatus
    input_schema: dict[str, str]
    spec: PolicyDefinitionDict
    requirements: list[str]
    archived: bool
    variables: list[str] | None = None
    created_at: datetime
    last_updated_at: datetime
    ui_metadata: dict[str, UIMetadata] | None = None

    class Config:
        from_attributes = True


class ConfigurationVariablesBase(BaseModel):
    name: str
    value: str | float | int | bool | None = None


class ConfigurationVariables(ConfigurationVariablesBase):
    created_at: datetime | None = None
    last_updated_at: datetime | None = None


class RunUpdate(BaseModel):
    status: str
    result: str
    run_metadata: dict | None = None


class Run(BaseModel):
    run_id: UUID
    policy_version_id: UUID
    run_group_id: UUID | None = None
    status: str
    result: str | None = None
    run_metadata: dict | None = None
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class RunResult(BaseModel):
    run_id: UUID
    status: str
    result: str | None = None
    run_metadata: dict | None = None


class StepMetadataBase(BaseModel):
    step_name: str
    node_type: str
    start_time: float
    end_time: float
    error: str | list[str] | None = None
    extra: dict | None = None


class StepMetadata(StepMetadataBase):
    step_metadata_id: UUID
    run_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class _StepDetails(BaseModel):
    output: bytes | str | dict | list | int | float | None
    metadata: StepMetadataBase | None


class RunData(BaseModel):
    run_id: UUID
    policy_version_id: UUID
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


class DataSource(DataSourceSpec):
    data_source_id: UUID
    archived: bool
    created_at: datetime
    last_updated_at: datetime
    variables: list[str] | None = None
    runtime_params: list[str] | None = None

    @classmethod
    def from_orm(cls, data) -> "DataSource":
        spec = data.to_spec()
        return cls(
            data_source_id=data.data_source_id,
            archived=data.archived,
            created_at=data.created_at,
            last_updated_at=data.last_updated_at,
            variables=data.variables,
            runtime_params=data.runtime_params,
            **spec.model_dump(),
        )


class DataSourceEnvVarBase(BaseModel):
    name: str
    value: str | float | int | bool | None = None


class DataSourceEnvVar(DataSourceEnvVarBase):
    created_at: datetime | None = None
    last_updated_at: datetime | None = None

    class Config:
        from_attributes = True


class DataSourceReference(BaseModel):
    data_source_id: UUID
    name: str
    created_at: datetime


class DataObjectMetadata(BaseModel):
    data_object_id: UUID
    data_source_id: UUID
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
    configured_params: dict[str, Any]
    run_id: str


class DataBrokerResponse(BaseModel):
    data_object_id: UUID
    origin: DataObjectOrigin
    key: str
    value: Any


class Backfill(BaseModel):
    backfill_id: UUID
    backtest_id: UUID
    status: RunStatus
    config_variables: dict | None

    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class BackfillStatus(BaseModel):
    backfill_id: UUID
    status: RunStatus
    config_variables: dict | None


class Backtest(BaseModel):
    backtest_id: UUID
    policy_version_id: UUID
    input_file_id: UUID
    environments: list[dict]
    status: JobStatus
    calculate_metrics: bool
    target_column: str | None
    time_column: str | None
    group_by_columns: list[str] | None

    created_at: datetime
    last_updated_at: datetime


class BacktestStatus(BaseModel):
    backtest_id: UUID
    status: JobStatus
    backfills: list[BackfillStatus]


class UploadedFile(BaseModel):
    uploaded_file_id: UUID
    file_name: str | None = None
    file_schema: dict[str, str]
    created_at: datetime

    class Config:
        from_attributes = True


class BeamWorkspace(BaseModel):
    policy_version_id: UUID
    status: str

    class Config:
        from_attributes = True


class BacktestMetrics(BaseModel):
    backtest_id: UUID
    status: RunStatus
    metrics: list[dict] | None = None


class BacktestMetricsConfig(BaseModel):
    target_column: str
    time_column: str | None = None
    group_by_columns: list[str] | None = None
    group_by_columns: list[str] | None = None
