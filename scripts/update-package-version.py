#!/usr/bin/env python3
"""
Update package version in pyproject.toml files.

This script updates the version field in pyproject.toml files to support
automated PyPI publishing with development and release versions.

Development versions use PEP 440 compliant format: <version>.dev<timestamp>
The timestamp ensures uniqueness and proper version ordering on PyPI.

Usage:
    # Generate and print dev version (without updating files)
    python scripts/update-package-version.py --dev --print-only

    # Set specific version for packages
    python scripts/update-package-version.py vulkan vulkan-engine --version 1.0.0

    # Generate dev version for both packages
    python scripts/update-package-version.py vulkan vulkan-engine --dev

    # Print release version (strips 'v' prefix)
    python scripts/update-package-version.py --version v1.2.3 --print-only

    # Validate package versions match a tag version
    python scripts/update-package-version.py vulkan vulkan-engine --version v1.2.3 --validate
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def read_current_version(pyproject_path: Path) -> str:
    """Read current version from pyproject.toml."""
    content = pyproject_path.read_text()
    match = re.search(r'^version = "([^"]+)"$', content, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find version field in {pyproject_path}")
    return match.group(1)


def validate_versions(
    packages: list[str], expected_version: str, root_dir: Path
) -> None:
    """
    Validate that package versions match the expected version.

    Args:
        packages: List of package names to validate (e.g., ['vulkan', 'vulkan-engine'])
        expected_version: Expected version string
        root_dir: Root directory of the project

    Raises:
        SystemExit: If any package version doesn't match
    """
    # Strip 'v' prefix if present (for git tags like v1.0.0)
    if expected_version.startswith("v"):
        expected_version = expected_version[1:]

    print(f"Validating that package versions match: {expected_version}")

    mismatches = []
    for package in packages:
        package_dir = root_dir / package
        pyproject_path = package_dir / "pyproject.toml"

        if not pyproject_path.exists():
            print(f"✗ Error: {pyproject_path} not found", file=sys.stderr)
            sys.exit(1)

        current_version = read_current_version(pyproject_path)
        print(f"  {package}/pyproject.toml version: {current_version}")

        if current_version != expected_version:
            mismatches.append((package, current_version))

    if mismatches:
        print("\n✗ Version mismatch detected:", file=sys.stderr)
        for package, version in mismatches:
            print(
                f"  {package}/pyproject.toml has version {version}, expected {expected_version}",
                file=sys.stderr,
            )
        sys.exit(1)

    print(f"✓ All package versions match {expected_version}")


def generate_dev_version(base_version: str) -> str:
    """
    Generate PEP 440 compliant development version for PyPI.

    Format: <base-version>.dev<timestamp>
    Example: 0.1.0.dev20250105123045

    Note: The timestamp provides sufficient uniqueness and proper version ordering.
    Local version identifiers (e.g., +commit_hash) are not allowed on PyPI.
    """
    # Strip any existing dev/local version identifiers
    base_version = re.sub(r"\.dev.*", "", base_version)
    base_version = re.sub(r"\+.*", "", base_version)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{base_version}.dev{timestamp}"


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
        nargs="*",
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
        "--print-only",
        action="store_true",
        help="Only print the version without updating files (use with --dev or --version)",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate that package versions match the specified --version (requires packages and --version)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.validate and args.dev:
        parser.error("--validate cannot be used with --dev")
    if args.validate and not args.version:
        parser.error("--validate requires --version")
    if args.validate and not args.packages:
        parser.error("--validate requires package names")
    if not args.print_only and not args.validate and not args.packages:
        parser.error(
            "packages argument is required unless --print-only or --validate is used"
        )

    # Determine the root directory (script is in scripts/ subdirectory)
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # If validate mode, validate and exit
    if args.validate:
        validate_versions(args.packages, args.version, root_dir)
        sys.exit(0)

    # Determine the version
    if args.dev:
        # For dev versions, read base version from vulkan package
        vulkan_pyproject = root_dir / "vulkan" / "pyproject.toml"
        if not vulkan_pyproject.exists():
            print(f"✗ Error: {vulkan_pyproject} not found", file=sys.stderr)
            sys.exit(1)
        base_version = read_current_version(vulkan_pyproject)
        new_version = generate_dev_version(base_version)
    else:
        # Use specified version
        new_version = args.version
        # Strip 'v' prefix if present (for git tags like v1.0.0)
        if new_version.startswith("v"):
            new_version = new_version[1:]

    # If print-only mode, just print the version and exit
    if args.print_only:
        print(new_version)
        sys.exit(0)

    # Process each package
    for package in args.packages:
        package_dir = root_dir / package
        pyproject_path = package_dir / "pyproject.toml"

        if not pyproject_path.exists():
            print(f"✗ Error: {pyproject_path} not found", file=sys.stderr)
            sys.exit(1)

        # Update the version
        update_version(pyproject_path, new_version)

    print(f"\n✓ Successfully updated {len(args.packages)} package(s)")


if __name__ == "__main__":
    main()
