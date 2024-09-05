set -ex
name=$1
workspace_path=$2

venv_name=${VULKAN_VENVS_PATH}/${name}
uv venv ${venv_name}
source ${venv_name}/bin/activate
# TODO: This is a hack to install vulkan package from local source
uv pip install /tmp/vulkan/

# Install dependencies and the policy itself
cd ${workspace_path}

# TODO: This may fail to install the vulkan package
# while the vulkan library is installed from local.
# uv pip install -r pyproject.toml 
uv pip install .