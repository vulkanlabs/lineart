set -ex
NAME=$1
WORKSPACE_PATH=$2
VENV=/opt/venvs/$NAME
uv venv $VENV
source $VENV/bin/activate
uv pip install /tmp/vulkan_dagster/

cd $DAGSTER_HOME/workspaces/$NAME/$WORKSPACE_PATH

if [ -e requirements.txt ]; then
    uv pip install -r requirements.txt
fi