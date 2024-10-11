import argparse
import os
import sys

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_auth_id", type=str, help="User auth id")
    parser.add_argument("--name", type=str, default="test_user", help="User name")
    parser.add_argument("--email", type=str, default="test@mail.com", help="User email")
    parser.add_argument(
        "--project_name", type=str, default="myproject", help="Project name"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    VULKAN_SERVER_URL = os.getenv("VULKAN_SERVER_URL", "http://localhost:6001")

    print("Creating test project")
    response = requests.post(
        f"{VULKAN_SERVER_URL}/projects/",
        json={"name": args.project_name},
        headers={"Content-Type": "application/json"},
    )
    data = response.json()
    print(data)
    project_id = data.get("project_id")

    print(f"Creating user for user {args.user_auth_id}")
    response = requests.post(
        f"{VULKAN_SERVER_URL}/users/",
        json={
            "user_auth_id": args.user_auth_id,
            "name": args.name,
            "email": args.email,
        },
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
