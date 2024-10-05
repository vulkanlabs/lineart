workspace_name=$1
component_path=$2

venv_name=${VULKAN_VENVS_PATH}/${workspace_name}
source $venv_name/bin/activate
uv pip install ${component_path}