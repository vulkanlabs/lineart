venv_name=/opt/venvs/$2
source $venv_name/bin/activate
uv pip install $DAGSTER_HOME/components/$1