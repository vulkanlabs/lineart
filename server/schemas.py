from datetime import datetime

from pydantic import BaseModel


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
    component_id: int

    class Config:
        from_attributes = True


class ComponentVersionBase(BaseModel):
    alias: str
    input_schema: str
    output_schema: str
    repository: str


class ComponentVersion(ComponentVersionBase):
    component_id: int
    component_version_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyVersionBase(BaseModel):
    policy_id: int
    repository: str
    repository_version: str
    entrypoint: str
    alias: str | None = None


class PolicyVersion(PolicyVersionBase):
    policy_version_id: int
    created_at: datetime
    last_updated_at: datetime
    component_version_ids: list[int] | None = None

    class Config:
        from_attributes = True


class RunBase(BaseModel):
    status: str
    result: str | None = None


class Run(RunBase):
    run_id: int
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
