venv_name=${VULKAN_VENVS_PATH}/$2
source $venv_name/bin/activate
uv pip install $VULKAN_HOME/components/$1