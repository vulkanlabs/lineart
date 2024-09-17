from datetime import datetime

from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str


class Project(ProjectBase):
    project_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    user_auth_id: str
    email: str
    name: str


class User(UserBase):
    user_id: str
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class ProjectUserCreate(BaseModel):
    user_id: str
    role: str


class ProjectUserBase(ProjectUserCreate):
    project_id: str


class ProjectUser(ProjectUserBase):
    project_user_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyBase(BaseModel):
    name: str
    description: str
    input_schema: str
    output_schema: str
    active_policy_version_id: int | None = None


class PolicyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active_policy_version_id: int | None = None


class Policy(PolicyBase):
    policy_id: int
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class ComponentBase(BaseModel):
    name: str


class Component(ComponentBase):
    component_id: str
    project_id: str

    class Config:
        from_attributes = True


class ComponentVersionCreate(BaseModel):
    alias: str
    repository: str


class ComponentVersion(BaseModel):
    component_id: str
    component_version_id: str
    alias: str
    input_schema: str
    instance_params_schema: str
    node_definitions: str
    created_at: datetime
    output_schema: str | None = None
    project_id: str

    class Config:
        from_attributes = True


class ComponentVersionDependencyExpanded(BaseModel):
    component_id: str
    component_name: str
    component_version_id: str
    component_version_alias: str
    policy_id: int
    policy_version_id: int
    policy_name: str
    policy_version_alias: str


class PolicyVersionBase(BaseModel):
    policy_id: int
    alias: str | None = None


class PolicyVersionCreate(PolicyVersionBase):
    repository: str
    repository_version: str


class PolicyVersion(PolicyVersionBase):
    policy_version_id: int
    graph_definition: str
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class Run(BaseModel):
    run_id: int
    policy_version_id: int
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


class StepMetadata(StepMetadataBase):
    step_metadata_id: int
    run_id: int
    created_at: datetime

    class Config:
        from_attributes = True
