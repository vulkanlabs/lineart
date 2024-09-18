import sys

import requests

user_auth_id = sys.argv[1]

print("Creating test project")
response = requests.post(
    "http://localhost:6001/projects/",
    json={"name": "myproject"},
    headers={"Content-Type": "application/json"},
)
data = response.json()
print(data)
project_id = data.get("project_id")

print(f"Creating user for user {user_auth_id}")
response = requests.post(
    "http://localhost:6001/users/",
    json={"user_auth_id": user_auth_id, "name": "test_user", "email": "test@mail.com"},
    headers={"Content-Type": "application/json"},
)
data = response.json()
print(data)
user_id = data.get("user_id")

print(f"Adding user {user_id} to project {project_id}")
response = requests.post(
    f"http://localhost:6001/projects/{project_id}/users",
    json={"user_id": user_id, "role": "ADMIN"},
    headers={"Content-Type": "application/json"},
)
if response.status_code != 200:
    print(response.json())
    sys.exit(1)
