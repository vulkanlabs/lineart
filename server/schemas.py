from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class PolicyBase(BaseModel):
    name: str
    description: str
    input_schema: str
    output_schema: str
    active_policy_version_id: Optional[int] = None


class Policy(PolicyBase):
    policy_id: int
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class PolicyVersionBase(BaseModel):
    policy_id: int
    repository: str
    repository_version: str
    entrypoint: str
    alias: Optional[str] = None


class PolicyVersion(PolicyVersionBase):
    policy_version_id: int
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


class RunBase(BaseModel):
    policy_version_id: int
    status: str
    dagster_run_id: Optional[str] = None
    result: Optional[str] = None


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
    error: Optional[str] = None


class StepMetadata(StepMetadataBase):
    step_metadata_id: int
    run_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Component(BaseModel):
    name: str
    repository: bytes
