from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


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
    input_schema: str
    output_schema: str
    active_policy_version_id: UUID | None = None


class PolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active_policy_version_id: UUID | None = None


class Policy(PolicyBase):
    policy_id: UUID
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class ComponentBase(BaseModel):
    name: str


class Component(ComponentBase):
    component_id: UUID
    project_id: UUID

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
    graph_definition: str
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class Run(BaseModel):
    run_id: UUID
    policy_version_id: UUID
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
    last_updated_at: datetime
    steps: dict[str, _StepDetails]

    class Config:
        from_attributes = True
