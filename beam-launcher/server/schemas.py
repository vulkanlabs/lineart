from pydantic import BaseModel, Field


class BacktestConfig(BaseModel):
    project_id: str
    policy_version_id: str
    backtest_id: str
    data_sources: dict[str, str]
    config_variables: dict[str, str] = Field(default_factory=dict)
