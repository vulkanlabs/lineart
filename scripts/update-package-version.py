#!/usr/bin/env python3
"""
Update package version in pyproject.toml files.

This script updates the version field in pyproject.toml files to support
automated PyPI publishing with development and release versions.

Usage:
    # Generate dev version with timestamp and commit hash
    python scripts/update-package-version.py vulkan --dev --commit abc123

    # Set specific version (for tagged releases)
    python scripts/update-package-version.py vulkan --version 1.0.0

    # Generate dev version for both packages
    python scripts/update-package-version.py vulkan vulkan-engine --dev --commit abc123
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


def read_current_version(pyproject_path: Path) -> str:
    """Read current version from pyproject.toml."""
    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]+)"$', content, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find version field in {pyproject_path}")
    return match.group(1)


def generate_dev_version(base_version: str, commit_hash: str) -> str:
    """
    Generate PEP 440 compliant development version.

    Format: <base-version>.dev<timestamp>+<commit-hash>
    Example: 0.1.0.dev20250105123045+32a3603b
    """
    # Strip any existing dev/local version identifiers
    base_version = re.sub(r"\.dev.*", "", base_version)
    base_version = re.sub(r"\+.*", "", base_version)

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{base_version}.dev{timestamp}+{commit_hash}"


def update_version(pyproject_path: Path, new_version: str) -> None:
    """Update version in pyproject.toml file."""
    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    content = pyproject_path.read_text()

    # Update version line
    updated = re.sub(
        r'^version = ".*"$', f'version = "{new_version}"', content, flags=re.MULTILINE
    )

    if content == updated:
        raise ValueError(f"Failed to update version in {pyproject_path}")

    pyproject_path.write_text(updated)
    print(
        f"✓ Updated {pyproject_path.parent.name}/pyproject.toml to version {new_version}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Update package version in pyproject.toml files"
    )
    parser.add_argument(
        "packages",
        nargs="+",
        help="Package name(s) to update (e.g., vulkan, vulkan-engine)",
    )

    version_group = parser.add_mutually_exclusive_group(required=True)
    version_group.add_argument(
        "--version", help="Set specific version (for tagged releases)"
    )
    version_group.add_argument(
        "--dev", action="store_true", help="Generate development version with timestamp"
    )

    parser.add_argument(
        "--commit", help="Commit hash to include in version (required with --dev)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.dev and not args.commit:
        parser.error("--commit is required when using --dev")

    # Determine the root directory (script is in scripts/ subdirectory)
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Process each package
    for package in args.packages:
        package_dir = root_dir / package
        pyproject_path = package_dir / "pyproject.toml"

        if not pyproject_path.exists():
            print(f"✗ Error: {pyproject_path} not found", file=sys.stderr)
            sys.exit(1)

        if args.dev:
            # Read current base version and generate dev version
            base_version = read_current_version(pyproject_path)
            new_version = generate_dev_version(base_version, args.commit)
        else:
            # Use specified version
            new_version = args.version
            # Strip 'v' prefix if present (for git tags like v1.0.0)
            if new_version.startswith("v"):
                new_version = new_version[1:]

        # Update the version
        update_version(pyproject_path, new_version)

    print(f"\n✓ Successfully updated {len(args.packages)} package(s)")


if __name__ == "__main__":
    main()
