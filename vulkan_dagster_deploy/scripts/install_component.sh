VENV=/opt/venvs/$2
source $VENV/bin/activate
pip install $DAGSTER_HOME/components/$1