set -ex
workspace_path=$1
requirements=$2

cd ${workspace_path}
uv add ${requirements}
uv sync