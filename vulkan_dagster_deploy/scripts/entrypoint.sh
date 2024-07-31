# Start server to manage workspaces
fastapi dev "$VULKAN_HOME/app.py" --host 0.0.0.0 --port $VULKAN_PORT --no-reload &

# Start dagster webserver
cd $DAGSTER_HOME; dagster-webserver -h 0.0.0.0 -p $DAGSTER_PORT &
wait