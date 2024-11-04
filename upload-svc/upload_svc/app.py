import json
import os
from io import BytesIO

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, UploadFile
from vulkan.backtest.definitions import SupportedFileFormat

from upload_svc import schemas
from upload_svc.logger import init_logger
from upload_svc.manager.base import FileManager
from upload_svc.manager.gcs import GCSFileManager
from upload_svc.manager.local import LocalFileManager

logger = init_logger("upload-svc")

app = FastAPI()


def _get_file_manager():
    MANAGER_TYPE = os.environ.get("FILE_MANAGER_TYPE")
    match MANAGER_TYPE:
        case "local":
            base_path = os.environ.get("LOCAL_FILE_MANAGER_BASE_PATH")
            if base_path is None:
                raise ValueError("LOCAL_FILE_MANAGER_BASE_PATH is required")

            return LocalFileManager(base_path=base_path)
        case "gcs":
            gcp_project = os.environ.get("GCS_FILE_MANAGER_GCP_PROJECT")
            bucket_name = os.environ.get("GCS_FILE_MANAGER_BUCKET_NAME")
            base_path = os.environ.get("GCS_FILE_MANAGER_BASE_PATH")
            if not all([gcp_project, bucket_name, base_path]):
                raise ValueError(
                    "GCS_FILE_MANAGER_GCP_PROJECT, GCS_FILE_MANAGER_BUCKET_NAME, "
                    "and GCS_FILE_MANAGER_BASE_PATH are required"
                )

            return GCSFileManager(
                gcp_project=gcp_project,
                bucket_name=bucket_name,
                base_path=base_path,
            )
        case _:
            raise ValueError(f"Unsupported file manager type: {MANAGER_TYPE}")


@app.post(
    "/file",
    response_model=schemas.FileIdentifier,
)
async def validate_and_publish(
    project_id: str,
    file_format: SupportedFileFormat,
    schema: str,
    input_file: UploadFile,
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
