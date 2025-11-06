# FIXME: the `from_orm` methods in this file would cause circular imports
# if properly typed with db classes.
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field
from vulkan.core.run import RunStatus, WorkflowStatus
from vulkan.data_source import DataSourceStatus
from vulkan.schemas import DataSourceSpec, PolicyAllocationStrategy
from vulkan.spec.policy import PolicyDefinitionDict


class PolicyCreate(BaseModel):
    name: str
    description: str = ""


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


class WorkflowBase(BaseModel):
    spec: PolicyDefinitionDict
    requirements: list[str]
    variables: list[str] | None = None
    ui_metadata: dict[str, UIMetadata] | None = None


class Workflow(WorkflowBase):
    workflow_id: UUID
    status: WorkflowStatus

    @classmethod
    def from_orm(cls, workflow) -> "Workflow":
        if workflow is None:
            return None

        return cls(
            workflow_id=workflow.workflow_id,
            requirements=workflow.requirements,
            spec=workflow.spec,
            variables=workflow.variables,
            ui_metadata=workflow.ui_metadata,
            status=workflow.status,
        )


class ComponentBase(BaseModel):
    name: str
    description: str | None = None
    icon: str | None = None  # Base64 encoded image


class ComponentUpdate(ComponentBase):
    workflow: WorkflowBase | None = None


class Component(ComponentBase):
    component_id: UUID
    archived: bool
    created_at: datetime
    last_updated_at: datetime
    workflow: Workflow | None = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, component, workflow) -> "Component":
        return cls(
            name=component.name,
            description=component.description,
            icon=component.icon,
            component_id=component.component_id,
            archived=component.archived,
            created_at=component.created_at,
            last_updated_at=component.last_updated_at,
            workflow=Workflow.from_orm(workflow),
        )


class PolicyVersionUpdate(BaseModel):
    alias: str | None
    workflow: WorkflowBase


class PolicyVersionBase(BaseModel):
    policy_id: UUID
    alias: str | None


class PolicyVersion(PolicyVersionBase):
    policy_version_id: UUID
    archived: bool
    created_at: datetime
    last_updated_at: datetime
    workflow: Workflow | None = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, policy_version, workflow) -> "PolicyVersion":
        return cls(
            policy_version_id=policy_version.policy_version_id,
            policy_id=policy_version.policy_id,
            alias=policy_version.alias,
            archived=policy_version.archived,
            created_at=policy_version.created_at,
            last_updated_at=policy_version.last_updated_at,
            workflow=Workflow.from_orm(workflow),
        )


class ConfigurationVariablesBase(BaseModel):
    name: str
    value: str | float | int | bool | None = None


class ConfigurationVariables(ConfigurationVariablesBase):
    created_at: datetime | None = None
    last_updated_at: datetime | None = None


class Run(BaseModel):
    run_id: UUID
    run_group_id: UUID | None = None
    policy_version_id: UUID
    status: RunStatus
    result: str | None = None
    input_data: dict | None = None
    run_metadata: dict | None = None
    created_at: datetime
    started_at: datetime | None = None
    last_updated_at: datetime

    class Config:
        from_attributes = True


class RunResult(BaseModel):
    run_id: UUID
    status: RunStatus
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


class StepDetails(BaseModel):
    output: bytes | str | dict | list | int | float | None
    metadata: StepMetadataBase | None


class RunData(Run):
    steps: dict[str, StepDetails] = Field(default_factory=dict)

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
    created_at: datetime
    last_updated_at: datetime
    variables: list[str] | None = None
    runtime_params: list[str] | None = None
    status: DataSourceStatus = DataSourceStatus.DRAFT

    @classmethod
    def from_orm(cls, data) -> "DataSource":
        spec = data.to_spec()
        return cls(
            data_source_id=data.data_source_id,
            created_at=data.created_at,
            last_updated_at=data.last_updated_at,
            variables=data.variables,
            runtime_params=data.runtime_params,
            status=data.status,
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


class DataSourceCredentialBase(BaseModel):
    credential_type: Literal["CLIENT_ID", "CLIENT_SECRET", "USERNAME", "PASSWORD"]
    value: str


class DataSourceCredential(DataSourceCredentialBase):
    credential_id: UUID
    data_source_id: UUID
    created_at: datetime
    last_updated_at: datetime

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
    start_time: float | None = None
    end_time: float | None = None
    error: dict | str | None = None


class RunGroupRuns(BaseModel):
    main: UUID
    shadow: list[UUID] | None = None


class RunGroupResult(BaseModel):
    policy_id: UUID
    run_group_id: UUID
    runs: RunGroupRuns


class RunCreated(BaseModel):
    policy_version_id: UUID
    run_id: UUID


class ConfigurationVariablesSetResult(BaseModel):
    policy_version_id: UUID
    variables: list[ConfigurationVariables]


class DataSourceTestRequest(BaseModel):
    """Full test request with all configuration (used for testing without existing data source)."""

    url: str
    method: str = "GET"
    headers: dict[str, str] | None = None
    body: dict[str, Any] | str | None = None
    params: dict[str, Any] | None = None
    env_vars: dict[str, str] | None = None


class DataSourceTestParams(BaseModel):
    """
    Parameters for testing an existing data source.
    Data source ID comes from URL path.
    """

    params: dict[str, Any] | None = None
    env_vars: dict[str, str] | None = None


class DataSourceTestRequestById(BaseModel):
    """
    Internal model with data source ID for service layer.
    """

    data_source_id: str
    params: dict[str, Any] | None = None
    env_vars: dict[str, str] | None = None


class DataSourceTestResponse(BaseModel):
    test_id: UUID
    request_url: str | None = None
    request_headers: dict[str, str] | None = None
    status_code: int | None
    response_time_ms: float
    response_body: dict[str, Any] | str | None = None
    response_headers: dict[str, str] | None = None
    error: str | None = None
