import base64
import logging
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI
from pydantic.dataclasses import dataclass
from vulkan.artifacts.gcs import GCSArtifactManager
from vulkan_public.exceptions import ConflictingDefinitionsError

from . import schemas
from .context import ExecutionContext
from .template import (
    GCPBuildManager,
    prepare_base_image_context,
    prepare_beam_image_context,
)
from .workspace import VulkanComponentManager, VulkanWorkspaceManager

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

VULKAN_HOME = os.getenv("VULKAN_HOME")
VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")
VULKAN_SERVER_PATH = os.getenv("VULKAN_SERVER_PATH")


def get_artifact_manager():
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not GCP_PROJECT_ID or not GCP_BUCKET_NAME or not GOOGLE_APPLICATION_CREDENTIALS:
        raise ValueError("GCP configuration missing")

    return GCSArtifactManager(
        project_id=GCP_PROJECT_ID,
        bucket_name=GCP_BUCKET_NAME,
        token=GOOGLE_APPLICATION_CREDENTIALS,
    )


def get_gcp_build_manager() -> GCPBuildManager:
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_REGION = os.getenv("GCP_REGION")
    GCP_REPOSITORY_NAME = os.getenv("GCP_REPOSITORY_NAME")

    if not GCP_PROJECT_ID or not GCP_REGION or not GCP_REPOSITORY_NAME:
        raise ValueError("GCP configuration missing")

    return GCPBuildManager(
        gcp_project_id=GCP_PROJECT_ID,
        gcp_region=GCP_REGION,
        gcp_repository_name=GCP_REPOSITORY_NAME,
    )


@dataclass
class ImageBuildConfig:
    python_version: str
    beam_sdk_version: str
    flex_template_base_image: str


def get_image_build_config():
    python_version = os.getenv("VULKAN_PYTHON_VERSION")
    beam_sdk_version = os.getenv("VULKAN_BEAM_SDK_VERSION")
    flex_template_base_image = os.getenv("VULKAN_FLEX_TEMPLATE_BASE_IMAGE")

    return ImageBuildConfig(
        python_version=python_version,
        beam_sdk_version=beam_sdk_version,
        flex_template_base_image=flex_template_base_image,
    )


@app.post("/workspaces/create")
def create_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    artifacts: GCSArtifactManager = Depends(get_artifact_manager),
    build_manager: GCPBuildManager = Depends(get_gcp_build_manager),
    image_build_config: ImageBuildConfig = Depends(get_image_build_config),
):
    """
    Create the dagster workspace and venv used to run a policy version.

    """
    logger.info(f"[{project_id}] Creating workspace: {name} (python_module)")
    vm = VulkanWorkspaceManager(project_id, name)

    with ExecutionContext(logger) as ctx:
        repository = base64.b64decode(repository)
        workspace_path = vm.unpack_workspace(repository)
        ctx.register_asset(workspace_path)

        venv_path = vm.create_venv()
        ctx.register_asset(venv_path)

        policy_definition_settings = vm.get_policy_definition_settings()
        required_components = policy_definition_settings["required_components"]
        # TODO Check components are available

        logger.info(f"[{project_id}] Installing workspace: {name}")
        vm.install_components(required_components)
        settings = vm.get_resolved_policy_settings()
        logger.info(f"[{project_id}] Successfully installed workspace: {name}")

        artifact_path = f"{project_id}/policy/{name}.tar.gz"
        artifacts.post(artifact_path, repository)

        # Build base image
        build_context_path = prepare_base_image_context(
            server_path=VULKAN_SERVER_PATH,
            workspace_name=vm.workspace_name,
            workspace_path=vm.workspace_path,
            components_path=vm.components_path,
            dependencies=required_components,
            python_version=image_build_config.python_version,
        )
        ctx.register_asset(build_context_path)
        upload_path = f"build_context/{name}.tar.gz"
        _ = artifacts.post_file(from_path=build_context_path, to_path=upload_path)
        image_path = build_manager.trigger_cloudbuild_job(
            bucket_name=artifacts.bucket_name,
            context_file=upload_path,
            image_name=name,
        )

    logger.info(f"Created workspace at: {workspace_path}")
    return {
        "policy_definition_settings": policy_definition_settings,
        "workspace_path": workspace_path,
        "graph_definition": settings["nodes"],
        "input_schema": settings["input_schema"],
        "data_sources": settings["data_sources"],
        "image_path": image_path,
    }


@app.post("/workspaces/beam/create")
def create_beam_workspace(
    name: Annotated[str, Body()],
    base_image: Annotated[str, Body()],
    artifacts: GCSArtifactManager = Depends(get_artifact_manager),
    build_manager: GCPBuildManager = Depends(get_gcp_build_manager),
    image_build_config: ImageBuildConfig = Depends(get_image_build_config),
):
    """
    Create the dagster workspace and venv used to run a policy version.
    """
    beam_image_name = f"{name}-beam"

    with ExecutionContext(logger) as ctx:
        # Build base image
        build_context_path = prepare_beam_image_context(
            name=beam_image_name,
            base_image=base_image,
            server_path=VULKAN_SERVER_PATH,
            python_version=image_build_config.python_version,
            beam_sdk_version=image_build_config.beam_sdk_version,
            flex_template_base_image=image_build_config.flex_template_base_image,
        )
        ctx.register_asset(build_context_path)
        upload_path = f"build_context/{beam_image_name}.tar.gz"
        _ = artifacts.post_file(from_path=build_context_path, to_path=upload_path)
        image_path = build_manager.trigger_cloudbuild_job(
            bucket_name=artifacts.bucket_name,
            context_file=upload_path,
            image_name=name,
            image_tag="beam",
        )

    return {
        "image_path": image_path,
    }


@app.post("/workspaces/delete")
def delete_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
):
    logger.info(f"[{project_id}] Deleting workspace: {name}")
    vm = VulkanWorkspaceManager(project_id, name)
    with ExecutionContext(logger):
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {name}")

    return {"workspace_path": vm.workspace_path}


@app.post("/components", response_model=schemas.ComponentConfig)
def create_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    artifacts: GCSArtifactManager = Depends(get_artifact_manager),
):
    logger.info(f"[{project_id}] Creating component version: {alias}")
    cm = VulkanComponentManager(
        project_id,
        alias,
    )

    with ExecutionContext(logger) as ctx:
        if os.path.exists(os.path.join(cm.components_path, alias)):
            raise ConflictingDefinitionsError("Component version already exists")

        repository = base64.b64decode(repository)
        component_path = cm.unpack_component(repository)
        logger.info(f"Unpacked and stored component spec at: {component_path}")
        ctx.register_asset(component_path)

        definition = cm.load_component_definition()
        artifact_path = f"{project_id}/component/{alias}.tar.gz"
        artifacts.post(artifact_path, repository)

    return definition


@app.post("/components/delete")
def delete_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
):
    logger.info(f"Deleting component version: {alias}")
    cm = VulkanComponentManager(project_id, alias)

    with ExecutionContext(logger):
        cm.delete_component()

    logger.info(f"Successfully deleted component version: {alias}")

    return {"component_alias": alias}
