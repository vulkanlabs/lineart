from pydantic import BaseModel


class BacktestConfig(BaseModel):
    project_id: str
    policy_version_id: str
    backtest_id: str
    image: str
    data_sources: dict
    config_variables: dict | None = None
