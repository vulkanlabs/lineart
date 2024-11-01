import json
from io import BytesIO

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, UploadFile
from vulkan.backtest.definitions import SupportedFileFormat

from upload_svc import schemas
from upload_svc.logger import init_logger
from upload_svc.manager.base import FileManager
from upload_svc.manager.local import LocalFileManager

logger = init_logger("upload-svc")

app = FastAPI()


def _get_file_manager():
    return LocalFileManager(base_dir="/opt/data")


@app.get("/file/id/{file_id}")
def get_file_info(file_id: str):
    return {"file_path": ...}


@app.post(
    "/file",
    response_model=schemas.FileIdentifier,
)
async def validate_and_publish(
    project_id: str,
    file_format: SupportedFileFormat,
    schema: str,
    input_file: UploadFile,
    config_variables: dict[str, str] | None = None,
    manager: FileManager = Depends(_get_file_manager),
):
    content = await input_file.read()
    try:
        data = _read_data(content, file_format)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"msg": str(e), "error": "INVALID_DATA"},
        )

    try:
        input_schema = json.loads(schema)
        _validate_schema(input_schema, data.columns)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"msg": str(e), "error": "INVALID_SCHEMA"},
        )

    try:
        file_path = manager.publish(project_id=project_id, data=data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"msg": str(e), "error": "FAILED_TO_PUBLISH"},
        )
    return schemas.FileIdentifier(file_path=file_path)


def _validate_schema(schema: dict[str, type], columns: list[str]) -> None:
    schema_columns = set(schema.keys())
    data_columns = set(columns)
    diff = schema_columns - data_columns

    # TODO: Check input schema is matched by uploaded data

    if len(diff) > 0:
        raise ValueError(f"Unmatched schema: missing columns {diff}")


def _read_data(content: bytes, file_format: SupportedFileFormat) -> pd.DataFrame:
    buf = BytesIO(content)
    match file_format:
        case SupportedFileFormat.CSV:
            data = pd.read_csv(buf)
        case SupportedFileFormat.PARQUET:
            data = pd.read_parquet(buf)
        case _:
            raise ValueError(f"Unsupported format {file_format}")

    return data
