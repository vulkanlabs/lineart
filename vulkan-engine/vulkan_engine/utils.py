import datetime
from typing import Any


def validate_date_range(
    start_date: datetime.date | None,
    end_date: datetime.date | None,
):
    if start_date is None:
        start_date = datetime.date.today() - datetime.timedelta(days=30)
    if end_date is None:
        end_date = datetime.date.today()
    return start_date, end_date


def convert_pydantic_to_dict(obj) -> Any:
    """Recursively convert Pydantic models to dictionaries."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: convert_pydantic_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_pydantic_to_dict(i) for i in obj]
    else:
        return obj
