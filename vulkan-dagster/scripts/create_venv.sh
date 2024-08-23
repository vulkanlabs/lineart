set -ex
name=$1
workspace_path=$2

venv_name=${VULKAN_VENVS_PATH}/${name}
uv venv ${venv_name}
source ${venv_name}/bin/activate
uv pip install /tmp/vulkan/

cd ${DAGSTER_HOME}/workspaces/${name}/${workspace_path}

if [ -e requirements.txt ]; then
    uv pip install -r requirements.txt
fi