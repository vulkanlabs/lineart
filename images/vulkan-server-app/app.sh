#!/bin/bash
set -ex

# Initialize database objects
python vulkan-server/vulkan_server/db.py

# Start the server
fastapi dev vulkan-server/vulkan_server/app.py --host 0.0.0.0 --port $APP_PORT
