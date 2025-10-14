set -ex
workspace_path=$1

# Install dependencies and the policy itself
uv init --bare ${workspace_path}
cd ${workspace_path}
uv add ${VULKAN_SERVER_PATH}/vulkan --extra hatchet
uv sync