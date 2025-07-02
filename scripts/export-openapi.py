#!/usr/bin/env python3
"""Export OpenAPI schema from Vulkan Server and Agent."""

import json
import shutil
import subprocess
from pathlib import Path


def export_server_spec():
    """Export OpenAPI spec from vulkan-server."""
    print("Exporting OpenAPI spec from vulkan-server...")

    from vulkan_server.app import app

    # Generate OpenAPI spec
    openapi_spec = app.openapi()

    # Ensure generated directory exists
    generated_dir = Path("generated")
    generated_dir.mkdir(exist_ok=True)

    # Write server OpenAPI spec
    server_spec_path = generated_dir / "openapi-server.json"
    with open(server_spec_path, "w") as f:
        json.dump(openapi_spec, f, indent=4)

    print(f"✅ Server OpenAPI spec exported to {server_spec_path}")
    return server_spec_path


def export_agent_spec():
    """Export OpenAPI spec from vulkan-agent."""
    print("Exporting OpenAPI spec from vulkan-agent...")

    from vulkan_agent.app import app

    # Generate OpenAPI spec
    openapi_spec = app.openapi()

    # Ensure generated directory exists
    generated_dir = Path("generated")
    generated_dir.mkdir(exist_ok=True)

    # Write agent OpenAPI spec
    agent_spec_path = generated_dir / "openapi-agent.json"
    with open(agent_spec_path, "w") as f:
        json.dump(openapi_spec, f, indent=4)

    print(f"✅ Agent OpenAPI spec exported to {agent_spec_path}")
    return agent_spec_path


def generate_typescript_types(spec_path: Path, output_dir: str, npm_name: str):
    """Generate TypeScript types from OpenAPI spec."""
    try:
        print(f"Generating TypeScript types for {npm_name}...")

        # Clean up and recreate output directory to avoid stale files
        output_path = Path("frontend") / "generated" / output_dir
        if output_path.exists():
            print(f"Cleaning up existing directory: {output_path}")
            shutil.rmtree(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate TypeScript types using npx for better robustness
        cmd = [
            "npx",
            "@openapitools/openapi-generator-cli",
            "generate",
            "-i",
            f"../{spec_path}",  # Relative to frontend directory
            "-g",
            "typescript-fetch",
            "-o",
            f"generated/{output_dir}",
            "--additional-properties=modelPropertyNaming=original",
            f"--additional-properties=npmName={npm_name}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd="frontend")

        if result.returncode == 0:
            print(f"✅ TypeScript types generated for {npm_name} in {output_path}")
        else:
            print(f"❌ Failed to generate TypeScript types for {npm_name}:")
            print(result.stderr)

    except Exception as e:
        print(f"❌ Error generating TypeScript types for {npm_name}: {e}")


def main():
    """Main export function."""
    print("🚀 Exporting OpenAPI specs and generating TypeScript types...")

    # Export both specs
    server_spec = export_server_spec()
    agent_spec = export_agent_spec()

    # Generate TypeScript types for each service in separate directories
    generate_typescript_types(server_spec, "server", "vulkan-server-api")
    generate_typescript_types(agent_spec, "agent", "vulkan-agent-api")

    print("🎉 OpenAPI export completed!")


if __name__ == "__main__":
    main()
