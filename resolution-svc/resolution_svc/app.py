import base64
import logging
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI
from vulkan.artifacts.gcs import GCSArtifactManager
from vulkan_public.exceptions import ConflictingDefinitionsError

from resolution_svc import schemas
from resolution_svc.build import (
    GCPBuildManager,
    get_gcp_build_manager,
    prepare_base_image_context,
    prepare_beam_image_context,
)
from resolution_svc.config import (
    VulkanConfig,
    get_artifact_manager,
    get_vulkan_config,
)
from resolution_svc.context import ExecutionContext
from resolution_svc.workspace import VulkanComponentManager, VulkanWorkspaceManager

app = FastAPI()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


@app.post("/workspaces/create")
def create_workspace(
    name: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
    artifacts: GCSArtifactManager = Depends(get_artifact_manager),
    build_manager: GCPBuildManager = Depends(get_gcp_build_manager),
):
    """
    Create the dagster workspace and venv used to run a policy version.

    """
    logger.info(f"[{project_id}] Creating workspace: {name} (python_module)")
    vm = VulkanWorkspaceManager(project_id, name, vulkan_config)

    with ExecutionContext(logger) as ctx:
        repository_data = base64.b64decode(repository)
        workspace_path = vm.unpack_workspace(repository_data)
        ctx.register_asset(workspace_path)

        venv_path = vm.create_venv()
        ctx.register_asset(venv_path)

        policy_definition_settings = vm.get_policy_definition_settings()
        required_components = policy_definition_settings["required_components"]

        logger.info(f"[{project_id}] Installing workspace: {name}")
        vm.install_components(required_components)
        settings = vm.get_resolved_policy_settings()
        logger.info(f"[{project_id}] Successfully installed workspace: {name}")

        artifact_path = f"{project_id}/policy/{name}.tar.gz"
        artifacts.post(artifact_path, repository_data)

        # Build base image
        build_context_path = prepare_base_image_context(
            server_path=vulkan_config.server_path,
            workspace_name=vm.workspace_name,
            workspace_path=vm.workspace_path,
            components_path=vm.components_path,
            dependencies=required_components,
            base_image=build_manager.base_image,
        )
        ctx.register_asset(build_context_path)
        upload_path = f"build_context/{name}.tar.gz"
        _ = artifacts.post_file(from_path=build_context_path, to_path=upload_path)
        image_path = build_manager.build_base_image(
            bucket_name=artifacts.bucket_name,
            context_file=upload_path,
            image_name=name,
            image_tag="base",
        )

    logger.info(f"Created workspace at: {workspace_path}")
    return {
        "policy_definition_settings": policy_definition_settings,
        "module_name": vm.code_location.module_name,
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
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
    artifacts: GCSArtifactManager = Depends(get_artifact_manager),
    build_manager: GCPBuildManager = Depends(get_gcp_build_manager),
):
    """
    Create the dagster workspace and venv used to run a policy version.
    """

    with ExecutionContext(logger) as ctx:
        # Build base image
        build_context_path = prepare_beam_image_context(
            name=name,
            base_image=base_image,
            server_path=vulkan_config.server_path,
        )
        ctx.register_asset(build_context_path)
        upload_path = f"build_context/beam/{name}.tar.gz"
        _ = artifacts.post_file(from_path=build_context_path, to_path=upload_path)
        image_path = build_manager.build_beam_image(
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
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.info(f"[{project_id}] Deleting workspace: {name}")
    vm = VulkanWorkspaceManager(project_id, name, vulkan_config)
    with ExecutionContext(logger):
        vm.delete_resources()

    logger.info(f"Successfully deleted workspace: {name}")

    return {"workspace_path": vm.workspace_path}


@app.post("/components", response_model=schemas.ComponentConfig)
def create_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    repository: Annotated[str, Body()],
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
    artifacts: GCSArtifactManager = Depends(get_artifact_manager),
):
    logger.info(f"[{project_id}] Creating component version: {alias}")
    cm = VulkanComponentManager(
        project_id,
        alias,
        vulkan_config,
    )

    with ExecutionContext(logger) as ctx:
        if os.path.exists(os.path.join(cm.components_path, alias)):
            raise ConflictingDefinitionsError("Component version already exists")

        repository_data = base64.b64decode(repository)
        component_path = cm.unpack_component(repository_data)
        logger.info(f"Unpacked and stored component spec at: {component_path}")
        ctx.register_asset(component_path)

        definition = cm.load_component_definition()
        artifact_path = f"{project_id}/component/{alias}.tar.gz"
        artifacts.post(artifact_path, repository_data)

    return definition


@app.post("/components/delete")
def delete_component(
    alias: Annotated[str, Body()],
    project_id: Annotated[str, Body()],
    vulkan_config: VulkanConfig = Depends(get_vulkan_config),
):
    logger.info(f"Deleting component version: {alias}")
    cm = VulkanComponentManager(project_id, alias, vulkan_config)

    with ExecutionContext(logger):
        cm.delete_component()

    logger.info(f"Successfully deleted component version: {alias}")

    return {"component_alias": alias}
