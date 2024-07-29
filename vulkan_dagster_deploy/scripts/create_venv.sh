set -ex
NAME=$1
WORKSPACE_PATH=$2
VENV=/opt/venvs/$NAME
python -m venv $VENV
source $VENV/bin/activate
pip install /tmp/vulkan_dagster/

cd $DAGSTER_HOME/workspaces/$NAME/$WORKSPACE_PATH

if [ -e requirements.txt ]; then
    pip install -r requirements.txt
fi