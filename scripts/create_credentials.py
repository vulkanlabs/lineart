import os
import sys

import requests

user_auth_id = sys.argv[1]
VULKAN_SERVER_URL = os.getenv("VULKAN_SERVER_URL", "http://localhost:6001")

print("Creating test project")
response = requests.post(
    f"{VULKAN_SERVER_URL}/projects/",
    json={"name": "myproject"},
    headers={"Content-Type": "application/json"},
)
data = response.json()
print(data)
project_id = data.get("project_id")

print(f"Creating user for user {user_auth_id}")
response = requests.post(
    f"{VULKAN_SERVER_URL}/users/",
    json={"user_auth_id": user_auth_id, "name": "test_user", "email": "test@mail.com"},
    headers={"Content-Type": "application/json"},
)
data = response.json()
print(data)
user_id = data.get("user_id")

print(f"Adding user {user_id} to project {project_id}")
response = requests.post(
    f"{VULKAN_SERVER_URL}/projects/{project_id}/users",
    json={"user_id": user_id, "role": "ADMIN"},
    headers={"Content-Type": "application/json"},
)
if response.status_code != 200:
    print(response.json())
    sys.exit(1)
