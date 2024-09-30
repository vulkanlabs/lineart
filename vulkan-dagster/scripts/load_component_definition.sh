set -x
scripts_path=$1
component_alias=$2
tmp_path=$3

venv_name=${VULKAN_VENVS_PATH}/${component_alias}

# Create a temporary virtual environment to load the component definition
uv venv ${venv_name}
source ${venv_name}/bin/activate

uv pip install ${VULKAN_HOME}/components/${component_alias}

python ${scripts_path}/load_component_definition.py \
    --alias ${component_alias} \
    --components_base_dir ${VULKAN_HOME}/components \
    --output_file ${tmp_path}

# Save the exit status of the script
exit_status=$?

deactivate

# Remove the temporary virtual environment
rm -rf ${venv_name}

exit ${exit_status}
