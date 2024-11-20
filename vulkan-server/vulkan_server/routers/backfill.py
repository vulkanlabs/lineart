import json
import os
from typing import Annotated
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from gcsfs import GCSFileSystem
from pyarrow import parquet
from sqlalchemy.orm import Session
from vulkan.backtest.definitions import SupportedFileFormat
from vulkan.core.run import RunStatus
from vulkan_public.spec.dependency import INPUT_NODE

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.beam.launcher import DataflowLauncher, get_launcher
from vulkan_server.config_variables import resolve_config_variables
from vulkan_server.db import (
    Backfill,
    BeamWorkspace,
    PolicyVersion,
    UploadedFile,
    WorkspaceStatus,
    get_db,
)
from vulkan_server.logger import init_logger
from vulkan_server.services.file_ingestion import VulkanFileIngestionServiceClient
from vulkan_server.services.resolution import (
    ResolutionServiceClient,
    get_resolution_service_client,
)

logger = init_logger("backfills")
router = APIRouter(
    prefix="/backfills",
    tags=["backfills"],
    responses={404: {"description": "Not found"}},
)

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_DATAFLOW_JOB_LOCATION = os.getenv("GCP_DATAFLOW_JOB_LOCATION")


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


@router.get("/", response_model=list[schemas.Backfill])
def list_backfills(project_id: str = Depends(get_project_id), db=Depends(get_db)):
    results = db.query(Backfill).filter_by(project_id=project_id).all()
    if len(results) == 0:
        return Response(status_code=204)
    return results


@router.get("/{backfill_id}", response_model=schemas.Backfill)
def get_backfill(
    backfill_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(backfill_id=backfill_id, project_id=project_id)
        .first()
    )
    if backfill is None:
        return Response(status_code=404)
    return backfill


@router.put("/{backfill_id}")
def update_backfill(
    backfill_id: str,
    status: RunStatus,
    results_path: str,
    db: Session = Depends(get_db),
    project_id: str = Depends(get_project_id),
):
    backfill = (
        db.query(Backfill)
        .filter_by(backfill_id=backfill_id, project_id=project_id)
        .first()
    )
    if backfill is None:
        return Response(status_code=404)

    backfill.status = status
    backfill.results_path = results_path
    db.commit()
    return backfill


@router.post("/", response_model=schemas.Backfill)
async def create_backfill(
    policy_version_id: UUID,
    input_file: UploadFile,
    file_format: SupportedFileFormat,
    name: str | None = None,
    config_variables: str | None = None,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    file_input_client=Depends(make_file_input_service),
    run_launcher: DataflowLauncher = Depends(get_launcher),
    resolution_service: ResolutionServiceClient = Depends(
        get_resolution_service_client
    ),
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

    if config_variables is not None:
        config_variables = json.loads(config_variables)

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

    backfill = Backfill(
        policy_version_id=policy_version_id,
        name=name,
        input_data_path=file_info["file_path"],
        status=RunStatus.PENDING,
        config_variables=resolved_config,
        project_id=project_id,
    )
    db.add(backfill)
    db.commit()

    try:
        workspace: BeamWorkspace = _ensure_beam_workspace(
            policy_version_id, project_id, db, resolution_service
        )
    except Exception as e:
        logger.error(f"Backfill launch failed: {e}")
        logger.error(
            "This is usually an issue with Vulkan's internal services. "
            "Contact support for assistance."
        )
        backfill.status = RunStatus.FAILURE
        db.commit()

    response = run_launcher.launch_run(
        policy_version_id=str(policy_version_id),
        project_id=str(project_id),
        backfill_id=str(backfill.backfill_id),
        image=workspace.image,
        module_name=policy_version.module_name,
        data_sources={
            INPUT_NODE: backfill.input_data_path,
        },
        config_variables=config_variables,
    )
    backfill.gcp_project_id = response.project_id
    backfill.gcp_job_id = response.job_id
    backfill.output_path = response.output_path
    db.commit()

    logger.info(f"Launched run {response}")

    return backfill


def _ensure_beam_workspace(
    policy_version_id: UUID,
    project_id: UUID,
    db: Session,
    resolution_service: ResolutionServiceClient,
):
    workspace = (
        db.query(BeamWorkspace).filter_by(policy_version_id=policy_version_id).first()
    )
    if workspace is None:
        try:
            logger.info(f"Creating workspace for policy version {policy_version_id}")
            workspace = _create_beam_workspace(
                policy_version_id, project_id, db, resolution_service
            )
        except Exception as e:
            msg = f"workspace: policy version {policy_version_id} failed"
            raise ValueError(msg) from e

    if workspace.status == WorkspaceStatus.CREATION_FAILED:
        raise ValueError(
            f"Workspace creation failed for policy version {policy_version_id}"
        )

    return workspace


def _create_beam_workspace(
    policy_version_id: UUID,
    project_id: UUID,
    db: Session,
    resolution_service: ResolutionServiceClient,
):
    policy_version: PolicyVersion = (
        db.query(PolicyVersion)
        .filter_by(project_id=project_id, policy_version_id=policy_version_id)
        .first()
    )
    beam_workspace = BeamWorkspace(
        policy_version_id=policy_version.policy_version_id,
        status=WorkspaceStatus.CREATION_PENDING,
    )
    db.add(beam_workspace)

    try:
        response = resolution_service.create_beam_workspace(
            policy_version_id=str(policy_version_id),
            base_image=policy_version.base_worker_image,
        )

        beam_workspace.image = response.json()["image_path"]
        beam_workspace.status = WorkspaceStatus.OK
    except Exception as e:
        beam_workspace.status = WorkspaceStatus.CREATION_FAILED
        raise e
    finally:
        db.commit()

    return beam_workspace


@router.get("/{backfill_id}/results")
def get_backfill_results(
    backfill_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    backfill = (
        db.query(Backfill)
        .filter_by(backfill_id=backfill_id, project_id=project_id)
        .first()
    )
    if backfill is None:
        return Response(status_code=404)
    # FIXME: check also that the status is "SUCCESS"

    try:
        results = _load_backfill_results(str(backfill.output_path))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "msg": (
                    "Failed to load backtest results. "
                    "This can happen if the backtest is still running or if there is an error."
                )
            },
        )

    return results.to_dict(orient="records")


def _load_backfill_results(results_path: str) -> pd.DataFrame:
    token_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    logger.info(f"Loading results from {results_path}")

    fs = GCSFileSystem(project=GCP_PROJECT_ID, access="read_write", token=token_path)
    files = fs.ls(results_path)

    if len(files) == 0:
        raise ValueError(f"No files found in {results_path}")

    ds = parquet.ParquetDataset(files, filesystem=fs)
    logger.info(f"Read {len(ds)} records from {results_path}")
    return ds.read().to_pandas()


@router.post("/files")
async def upload_file(
    file: Annotated[UploadFile, File()],
    file_format: Annotated[SupportedFileFormat, Form()],
    schema: Annotated[str, Form()],
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    file_input_client=Depends(make_file_input_service),
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
        project_id=project_id,
        file_path=file_info["file_path"],
        schema=schema,
    )
    db.add(uploaded_file)
    db.commit()

    return {"uploaded_file_id": uploaded_file.uploaded_file_id}
