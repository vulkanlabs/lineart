import json
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session
from vulkan.backtest.definitions import SupportedFileFormat
from vulkan.core.run import RunStatus

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.backtest.backtest import ensure_beam_workspace, resolve_backtest_envs
from vulkan_server.backtest.launcher import (
    BackfillLauncher,
    get_backfill_job_status,
    get_launcher,
)
from vulkan_server.backtest.results import ResultsDB, make_results_db
from vulkan_server.config_variables import _get_policy_version_defaults
from vulkan_server.db import (
    Backfill,
    Backtest,
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

logger = init_logger("backtests")
router = APIRouter(
    prefix="/backtests",
    tags=["backtests"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Backtest])
def list_backtests(project_id: str = Depends(get_project_id), db=Depends(get_db)):
    results = db.query(Backtest).filter_by(project_id=project_id).all()
    if len(results) == 0:
        return Response(status_code=204)
    return results


# TODO: Backtest Options (user defined, optional)
@router.post("/launch", response_model=schemas.Backtest)
def launch_backtest(
    policy_version_id: Annotated[str, Body()],
    input_file_id: Annotated[str, Body()],
    config_variables: Annotated[list[dict] | None, Body()],
    db: Session = Depends(get_db),
    project_id: str = Depends(get_project_id),
    run_launcher: BackfillLauncher = Depends(get_launcher),
):
    policy_version = (
        db.query(PolicyVersion)
        .filter_by(project_id=project_id, policy_version_id=policy_version_id)
        .first()
    )
    if policy_version is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Policy Version {policy_version_id} not found"},
        )

    try:
        workspace: BeamWorkspace = ensure_beam_workspace(policy_version_id, db)
    except Exception as e:
        logger.error(f"Backtest launch failed: {e}")
        raise HTTPException(
            status_code=400,
            detail={"msg": str(e)},
        )

    input_file = (
        db.query(UploadedFile)
        .filter_by(project_id=project_id, uploaded_file_id=input_file_id)
        .first()
    )
    if input_file is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Input File {input_file_id} not found"},
        )

    # Resolve Config Variables
    if config_variables is not None:
        policy_version_defaults = _get_policy_version_defaults(
            db=db,
            policy_version_id=policy_version_id,
            required_variables=policy_version.variables,
        )
        try:
            resolved_envs = resolve_backtest_envs(
                environments=config_variables,
                policy_version_defaults=policy_version_defaults,
                required_variables=policy_version.variables,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"msg": str(e)})
        except Exception as e:
            raise HTTPException(status_code=500, detail={"msg": str(e)})
    else:
        # No config variables provided, use defaults.
        resolved_envs = [{}]

    backtest = Backtest(
        project_id=project_id,
        policy_version_id=policy_version_id,
        input_file_id=input_file_id,
        environments=resolved_envs,
        status=RunStatus.PENDING,
    )
    db.add(backtest)
    db.commit()

    N = len(resolved_envs)
    for i, env in enumerate(resolved_envs, start=1):
        logger.debug(f"Launching backfill ({i / N})")
        backfill = run_launcher.create_backfill(
            project_id=project_id,
            backtest_id=backtest.backtest_id,
            workspace=workspace,
            policy_version=policy_version,
            input_data_path=input_file.file_path,
            resolved_config_variables=env,
        )
        logger.debug(f"Launched backfill ({i / N}): {backfill.backfill_id}")

    return backtest


@router.get("/{backtest_id}/status", response_model=list[schemas.BackfillStatus])
def get_backtest_status(
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
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Backtest {backtest_id} not found"},
        )

    backfills = (
        db.query(Backfill)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .all()
    )
    if len(backfills) == 0:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"No backfills found for backtest {backtest_id}"},
        )

    backtest_jobs = []

    for backfill in backfills:
        status = get_backfill_job_status(backfill.gcp_job_id)
        backtest_jobs.append(
            schemas.BackfillStatus(backfill_id=backfill.backfill_id, status=status)
        )

    return backtest_jobs


@router.post("/")
def create_workspace(
    policy_version_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    resolution_service: ResolutionServiceClient = Depends(
        get_resolution_service_client
    ),
):
    # If a workspace exists, this is a no-op.
    current_workspace = (
        db.query(BeamWorkspace).filter_by(policy_version_id=policy_version_id).first()
    )
    if current_workspace is not None:
        return current_workspace

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
        logger.error(f"Failed to create workspace ({policy_version_id}): {e}")
        msg = (
            "This is usually an issue with Vulkan's internal services. "
            "Contact support for assistance. "
            f"Workspace ID: {policy_version_id}"
        )
        raise HTTPException(status_code=500, detail={"msg": msg})
    finally:
        db.commit()

    return beam_workspace


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


@router.get("/{backtest_id}/results")
def get_backtest_results(
    backtest_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    results_db: ResultsDB = Depends(make_results_db),
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        raise HTTPException(
            status_code=404,
            detail={"msg": f"Backtest {backtest_id} not found"},
        )
    # TODO: check job status

    backfills = (
        db.query(Backfill)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .all()
    )

    data_paths = [job.output_path for job in backfills]
    logger.info(f"Loading backtest results: {data_paths}")
    try:
        results = results_db.load_data(data_paths)
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
        file_schema=schema,
    )
    db.add(uploaded_file)
    db.commit()

    return {"uploaded_file_id": uploaded_file.uploaded_file_id}
