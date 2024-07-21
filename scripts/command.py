import os
import subprocess
from argparse import ArgumentParser

from dotenv import load_dotenv


def launch_server(resource: str):
    if resource == "data":
        subprocess.run(
            [
                "flask",
                "--app",
                "test/resources/data_server.py",
                "run",
                "--port",
                os.getenv("TEST_DATA_SERVER_PORT"),
                "--debug",
            ]
        )


if __name__ == "__main__":
    load_dotenv()

    parser = ArgumentParser()
    command = parser.add_subparsers(dest="command", required=True)

    launch = command.add_parser("launch_server", help="Launch a server")
    launch.add_argument(
        "resource", type=str, choices=["dagster", "app", "client", "data"]
    )

    shutdown = command.add_parser("shutdown")
    shutdown.add_argument("resource", type=str)

    args = parser.parse_args()

    if args.command == "launch_server":
        launch_server(args.resource)
    else:
        raise ValueError(f"Unknown command: {args.command}")
