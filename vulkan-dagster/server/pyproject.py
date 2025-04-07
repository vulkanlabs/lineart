from pathlib import Path

import tomlkit


def get_pyproject(file_path: str) -> dict:
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"File {file_path} does not exist.")
    try:
        with open(file_path, "r") as f:
            pyproject = tomlkit.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse {file_path}: {e}")

    return pyproject


def set_dependencies(
    file_path: str,
    dependencies: list[str],
) -> None:
    pyproject = get_pyproject(file_path)
    if "project" not in pyproject:
        raise ValueError(f"Invalid pyproject file: {file_path}")

    pyproject["dependencies"] = dependencies
    with open(file_path, "w") as f:
        tomlkit.dump(pyproject, f)
