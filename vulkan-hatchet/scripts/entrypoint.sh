set -ex

# Start server to manage workspaces
fastapi dev "${VULKAN_SERVER_PATH}/vulkan-hatchet/server/app.py" --host 0.0.0.0 --port ${VULKAN_PORT} --no-reload &
wait