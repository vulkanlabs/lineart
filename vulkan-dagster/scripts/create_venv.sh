set -ex
name=$1
workspace_path=$2

venv_name=${VULKAN_VENVS_PATH}/${name}
uv venv ${venv_name}
source ${venv_name}/bin/activate
# TODO: This is a hack to install vulkan package from local source
uv pip install /tmp/vulkan/

cd ${workspace_path}

if [ -e requirements.txt ]; then
    uv pip install -r requirements.txt
fi