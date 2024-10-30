from fastapi import APIRouter, Depends, HTTPException, Response

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.db import (
    Backtest,
    Policy,
    PolicyVersion,
    get_db,
)
from vulkan_server.logger import init_logger
from vulkan_server.services import VulkanFileIngestionServiceClient

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
        server_url=server_config.server_url,
    )


@router.get("/", response_model=schemas.Backtest)
def list_backtests(project_id: str = Depends(get_project_id), db=Depends(get_db)):
    results = db.query(Backtest).filter_by(project_id=project_id).all()
    if len(results) == 0:
        return Response(status_code=204)
    return results


@router.get("/{backtest_id}", response_model=schemas.Backtest)
def get_backtest(
    backtest_id: str, project_id: str = Depends(get_project_id), db=Depends(get_db)
):
    backtest = (
        db.query(Backtest)
        .filter_by(backtest_id=backtest_id, project_id=project_id)
        .first()
    )
    if backtest is None:
        return Response(status_code=404)
    return backtest


@router.post("/", response_model=schemas.Backtest)
def create_backtest(
    config: schemas.BacktestRequest,
    project_id: str = Depends(get_project_id),
    db=Depends(get_db),
    file_input_client=Depends(make_file_input_service),
):
    policy_version: PolicyVersion = (
        db.query(PolicyVersion)
        .filter_by(project_id=project_id, policy_version_id=config.policy_version_id)
        .first()
    )
    if policy_version is None:
        raise HTTPException(
            status_code=400,
            detail={"msg": f"Invalid policy_version_id {config.policy_version_id}"},
        )

    policy: Policy = db.query(Policy).filter_by(
        project_id=project_id, policy_id=policy_version.policy_id
    ).first()

    try:
        file_id, valid = file_input_client.validate_and_publish(
            file_format=config.file_format,
            content=config.input_file,
            schema=policy.input_schema,
            config_variables=config.config_variables,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})

    if not valid:
        raise HTTPException(
            status_code=400,
            detail={"msg": "Input data did not match the input schema for the policy"},
        )

    backtest = Backtest(
        policy_version_id=config.policy_version_id,
        name=config.name,
        input_data_path=file_id,
        # config_variables=config.config_variables,
    )
    db.add(backtest)
    db.commit()

    return backtest
