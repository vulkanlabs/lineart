# Start server to manage workspaces
flask --app "$VULKAN_HOME/app.py" run --host 0.0.0.0 --port $VULKAN_PORT --debug --no-reload &

# Start dagster webserver
cd $DAGSTER_HOME; dagster-webserver -h 0.0.0.0 -p $DAGSTER_PORT &
wait