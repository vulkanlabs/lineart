# Start server to manage workspaces
poetry run flask --app "$VULKAN_HOME/app.py" run --host 0.0.0.0 --port $VULKAN_PORT --debug &

# Start dagster webserver
cd $DAGSTER_HOME; poetry run dagster-webserver -h 0.0.0.0 -p $DAGSTER_PORT &
wait