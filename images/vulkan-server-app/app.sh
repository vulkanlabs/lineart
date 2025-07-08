#!/bin/bash
set -ex

# Initialize database objects
python -m vulkan_server.database

# Start the server
fastapi dev vulkan-server/vulkan_server/app.py --host 0.0.0.0 --port $APP_PORT
