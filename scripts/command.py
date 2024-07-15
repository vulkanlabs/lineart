from argparse import ArgumentParser
from dotenv import load_dotenv

import os
import subprocess


def launch_server(args):
    if args.resource == "dagster":
        os.environ["DAGSTER_HOME"] = os.path.join(
            os.getcwd(), os.getenv("DAGSTER_HOME_DIR")
        )
        subprocess.run(["dagster", "dev", "-p", os.getenv("DAGSTER_PORT")])

    elif args.resource == "app":
        subprocess.run(
            [
                "flask",
                "--app",
                "server/app.py",
                "run",
                "--port",
                os.getenv("APP_PORT"),
                "--debug",
            ]
        )

    elif args.resource == "client":
        subprocess.run(
            [
                "flask",
                "--app",
                "test/resources/client_server.py",
                "run",
                "--port",
                os.getenv("TEST_CLIENT_SERVER_PORT"),
                "--debug",
            ]
        )

    elif args.resource == "data":
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


def shutdown_server(args):
    print(args)
    print("Shutting down servers")


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
        launch_server(args)
    elif args.command == "shutdown":
        shutdown_server(args)
    else:
        pass
