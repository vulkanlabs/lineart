import argparse
import json
import os

from vulkan_server.app import app

parser = argparse.ArgumentParser(prog="extract-openapi.py")
parser.add_argument("--out", help="Path to output file (JSON)", required=True)

if __name__ == "__main__":
    args = parser.parse_args()

    openapi = app.openapi()
    version = openapi.get("openapi", "unknown version")

    if not os.path.exists(os.path.dirname(args.out)):
        os.makedirs(os.path.dirname(args.out))

    print(f"writing openapi spec v{version}")
    with open(args.out, "w") as f:
        json.dump(openapi, f, indent=4)

    print(f"spec written to {args.out}")
