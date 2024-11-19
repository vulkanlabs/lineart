import os

from pydantic.dataclasses import dataclass
from vulkan.artifacts.gcs import GCSArtifactManager


@dataclass
class VulkanConfig:
    home: str
    venvs_path: str
    server_path: str


def get_vulkan_config() -> VulkanConfig:
    VULKAN_HOME = os.getenv("VULKAN_HOME")
    VULKAN_VENVS_PATH = os.getenv("VULKAN_VENVS_PATH")
    VULKAN_SERVER_PATH = os.getenv("VULKAN_SERVER_PATH")

    if not VULKAN_HOME or not VULKAN_VENVS_PATH or not VULKAN_SERVER_PATH:
        raise ValueError("Vulkan configuration missing")

    return VulkanConfig(
        home=VULKAN_HOME,
        venvs_path=VULKAN_VENVS_PATH,
        server_path=VULKAN_SERVER_PATH,
    )


def get_artifact_manager():
    return GCSArtifactManager(
        project_id=os.getenv("GCP_PROJECT_ID"),
        bucket_name=os.getenv("GCP_BUCKET_NAME"),
        token=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    )


@dataclass
class ImageBuildConfig:
    python_version: str
    beam_sdk_version: str
    flex_template_base_image: str


def get_image_build_config() -> ImageBuildConfig:
    python_version = os.getenv("VULKAN_PYTHON_VERSION")
    beam_sdk_version = os.getenv("VULKAN_BEAM_SDK_VERSION")
    flex_template_base_image = os.getenv("VULKAN_FLEX_TEMPLATE_BASE_IMAGE")

    if not python_version or not beam_sdk_version or not flex_template_base_image:
        raise ValueError(
            "Image build configuration missing: "
            "VULKAN_PYTHON_VERSION, VULKAN_BEAM_SDK_VERSION, VULKAN_FLEX_TEMPLATE_BASE_IMAGE"
        )

    return ImageBuildConfig(
        python_version=python_version,
        beam_sdk_version=beam_sdk_version,
        flex_template_base_image=flex_template_base_image,
    )
