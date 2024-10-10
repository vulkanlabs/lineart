import os
from argparse import ArgumentParser, Namespace

import pandas as pd
import requests


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description="Create users & projects from the Stack-Auth export CSV"
    )
    parser.add_argument("csv_path", help="Path to the CSV file")
    parser.add_argument(
        "--ignore-errors", dest="strict", action="store_false", help="Ignore errors"
    )

    return parser.parse_args()


def main():
    # Read the file with Pandas
    args = parse_args()
    df = pd.read_csv(args.csv_path)

    strict = args.strict

    column_map = {
        "id": "user_auth_id",
        "displayName": "name",
        "primaryEmail": "email",
    }

    df = df.rename(columns=column_map)
    df = df.loc[:, [k for k in column_map.values()]]
    df["project_name"] = df.loc[:, "user_auth_id"].apply(lambda x: x[:8])

    # Create the users
    VULKAN_SERVER_URL = os.getenv("VULKAN_SERVER_URL", "http://localhost:6001")
    for _, row in df.iterrows():
        print(f"creating user {row['email']}...")
        try:
            create_user(server_url=VULKAN_SERVER_URL, **row)
        except Exception as e:
            print(f"Failed to create user {row['email']}: {e}")
            if strict:
                raise e


def create_user(
    server_url: str, project_name: str, user_auth_id: str, name: str, email: str
):
    response = requests.post(
        f"{server_url}/projects/",
        json={"name": project_name},
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create project: {response.content}")

    data = response.json()
    project_id = data["project_id"]
    response = requests.post(
        f"{server_url}/users/",
        json={
            "user_auth_id": user_auth_id,
            "name": name,
            "email": email,
        },
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create user: {response.content}")

    data = response.json()
    user_id = data["user_id"]
    response = requests.post(
        f"{server_url}/projects/{project_id}/users",
        json={"user_id": user_id, "role": "ADMIN"},
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to add user to project: {response.content}")


if __name__ == "__main__":
    main()