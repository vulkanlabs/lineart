import json
from io import BytesIO
from typing import Annotated
from uuid import uuid4

import pandas as pd
from fastapi import Body, FastAPI, HTTPException, UploadFile
from vulkan.backtest.definitions import SupportedFileFormat

from upload_svc import schemas
from upload_svc.logger import init_logger

logger = init_logger("upload-svc")

app = FastAPI()


# TODO: take file as upload stream
@app.post(
    "/file",
    response_model=schemas.FileIdentifier,
)
async def validate_and_publish(
    file_format: SupportedFileFormat,
    schema: str,
    input_file: UploadFile,
    # config_variables: dict[str, str] | None = None,
):
    content = await input_file.read()
    try:
        data = _read_data(content, file_format)
        input_schema = json.loads(schema)
        _validate_schema(input_schema, data.columns)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"msg": str(e), "error": "INVALID"},
        )

    try:
        file_path = _publish(data)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"msg": str(e), "error": "FAILED_TO_PUBLISH"},
        )
    return schemas.FileIdentifier(file_path=file_path, file_id=uuid4())


def _validate_schema(schema, columns) -> bool:
    schema_columns = set(schema.keys())
    data_columns = set(columns)
    diff = schema_columns - data_columns

    if len(diff) > 0:
        raise ValueError(f"Unmatched schema: missing columns {diff}")


def _read_data(content:bytes, file_format: SupportedFileFormat) -> pd.DataFrame:
    buf = BytesIO(content)
    match file_format:
        case SupportedFileFormat.CSV:
            data = pd.read_csv(buf)
        case SupportedFileFormat.PARQUET:
            data = pd.read_parquet(buf)
        case _:
            raise ValueError(f"Unsupported format {file_format}")

    return data


def _publish(data: pd.DataFrame) -> str:
    file_path = "/opt/data-sample-test.parquet"
    data.to_parquet(file_path)
    return file_path
