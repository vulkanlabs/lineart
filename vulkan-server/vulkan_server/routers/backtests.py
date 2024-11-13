import os
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from gcsfs import GCSFileSystem
from pyarrow import parquet
from sqlalchemy.orm import Session
from vulkan.backtest.definitions import BacktestStatus, SupportedFileFormat
from vulkan_public.spec.dependency import INPUT_NODE

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.config_variables import resolve_config_variables
from vulkan_server.db import Backtest, PolicyVersion, get_db
from vulkan_server.logger import init_logger
from vulkan_server.services import (
    VulkanFileIngestionServiceClient,
    get_beam_launcher_client,
)

logger = init_logger("backtests")
router = APIRouter(
    prefix="/backtests",
    tags=["backtests"],
    responses={404: {"description": "Not found"}},
)


def make_file_input_service(
    project_id: str = Depends(get_project_id),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
) -> VulkanFileIngestionServiceClient:
    return VulkanFileIngestionServiceClient(
        project_id=project_id,
        server_url=server_config.upload_service_url,
    )


@router.get("/", response_model=list[schemas.Backtest])
def list_backtests(project_id: str = Depends(get_project_id), db=Depends(get_db)):
    results = db.query(Backtest).filter_by(project_id=project_id).all()
    if len(results) == 0:
        return Response(status_code=204)
    return results


@router.get("/{backtest_id}", response_model=schemas.Backtest)
def get_backtest(
    backtest_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        return Response(status_code=404)
    return backtest


@router.put("/{backtest_id}")
def update_backtest(
    backtest_id: str,
    status: BacktestStatus,
    results_path: str,
    db: Session = Depends(get_db),
    project_id: str = Depends(get_project_id),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        return Response(status_code=404)

    backtest.status = status
    backtest.results_path = results_path
    db.commit()
    return backtest


@router.post("/", response_model=schemas.Backtest)
async def create_backtest(
    policy_version_id: UUID,
    input_file: UploadFile,
    file_format: SupportedFileFormat,
    name: str | None = None,
    config_variables: dict[str, str] | None = None,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    file_input_client=Depends(make_file_input_service),
    beam_launcher_client=Depends(get_beam_launcher_client),
):
    policy_version: PolicyVersion = (
        db.query(PolicyVersion)
        .filter_by(project_id=project_id, policy_version_id=policy_version_id)
        .first()
    )
    if policy_version is None:
        raise HTTPException(
            status_code=400,
            detail={"msg": f"Invalid policy_version_id {policy_version_id}"},
        )

    resolved_config, missing = resolve_config_variables(
        db=db,
        policy_version_id=policy_version_id,
        required_variables=policy_version.variables,
        run_config_variables=config_variables,
    )
    if len(missing) > 0:
        raise HTTPException(
            status_code=400, detail={"msg": f"Mandatory variables not set: {missing}"}
        )

    try:
        content = await input_file.read()
        file_info = file_input_client.validate_and_publish(
            file_format=file_format,
            content=content,
            schema=policy_version.input_schema,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

    backtest = Backtest(
        policy_version_id=policy_version_id,
        name=name,
        input_data_path=file_info["file_path"],
        status=BacktestStatus.PENDING,
        config_variables=resolved_config,
        project_id=project_id,
    )
    db.add(backtest)
    db.commit()

    response = beam_launcher_client.launch_job(
        policy_version_id=str(policy_version_id),
        backtest_id=str(backtest.backtest_id),
        data_sources={
            INPUT_NODE: backtest.input_data_path,
        },
        config_variables=config_variables,
    )
    backtest.output_path = response.json()["output_path"]
    db.commit()

    return backtest


@router.get("/{backtest_id}/results")
def get_backtest_results(
    backtest_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        return Response(status_code=404)

    try:
        results = load_backtest_results(str(backtest.output_path))
    except Exception as e:
        return HTTPException(status_code=500, detail={"msg": str(e)})

    return results.to_dict(orient="records")


def load_backtest_results(results_path: str) -> pd.DataFrame:
    token_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    gcp_project = os.environ.get("GCP_PROJECT_ID")

    fs = GCSFileSystem(project=gcp_project, access="read_write", token=token_path)
    files = fs.ls(results_path)

    if len(files) == 0:
        raise ValueError(f"No files found in {results_path}")

    ds = parquet.ParquetDataset(files, filesystem=fs)
    return ds.read().to_pandas()
