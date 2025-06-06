import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from vulkan.core.backtest.definitions import SupportedFileFormat
from vulkan_server import definitions, schemas
from vulkan_server.db import UploadedFile, get_db
from vulkan_server.services.file_ingestion import VulkanFileIngestionServiceClient

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.UploadedFile])
def list_uploaded_files(
    db: Session = Depends(get_db),
):
    files = db.query(UploadedFile).all()
    if len(files) == 0:
        return Response(status_code=204)
    return files


def _make_file_input_service(
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
) -> VulkanFileIngestionServiceClient:
    return VulkanFileIngestionServiceClient(
        server_url=server_config.upload_service_url,
    )


@router.post("/", response_model=schemas.UploadedFile)
async def upload_file(
    file: Annotated[UploadFile, File()],
    file_format: Annotated[SupportedFileFormat, Form()],
    schema: Annotated[str, Form()],
    file_name: str | None = None,
    db: Session = Depends(get_db),
    file_input_client=Depends(_make_file_input_service),
):
    try:
        content = await file.read()
        schema = json.loads(schema)
        file_info = file_input_client.validate_and_publish(
            file_format=file_format,
            content=content,
            schema=schema,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

    uploaded_file = UploadedFile(
        file_name=file_name,
        file_path=file_info["file_path"],
        file_schema=schema,
    )
    db.add(uploaded_file)
    db.commit()

    return uploaded_file
