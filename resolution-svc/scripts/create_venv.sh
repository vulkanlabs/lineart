set -ex
venv_path=$1
workspace_path=$2

uv venv ${venv_path}
source ${venv_path}/bin/activate
# TODO: This is a hack to install vulkan package from local source
uv pip install --extra dagster -r ${VULKAN_SERVER_PATH}/vulkan/pyproject.toml
uv pip install ${VULKAN_SERVER_PATH}/vulkan

# Install dependencies and the policy itself
cd ${workspace_path}

# TODO: This may fail to install the vulkan package
# while the vulkan library is installed from local.
uv pip install .