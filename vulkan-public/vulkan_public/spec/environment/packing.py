import importlib.util
import os
import tarfile
from shutil import unpack_archive

ARCHIVE_FORMAT = "gztar"
TAR_FLAGS = "w:gz"
_EXCLUDE_PATHS = [".git", ".venv", ".vscode"]


def pack_workspace(name: str, repository_path: str):
    basename = f".tmp.{name}"
    # TODO: In the future we may want to have an ignore list
    filename = f"{basename}.{ARCHIVE_FORMAT}"
    with tarfile.open(name=filename, mode=TAR_FLAGS) as tf:
        for root, dirs, files in os.walk(repository_path):
            # TODO: match regex instead of exact path
            for path in _EXCLUDE_PATHS:
                if path in dirs:
                    dirs.remove(path)

            for file in files:
                file_path = os.path.join(root, file)
                tf.add(
                    file_path,
                    arcname=os.path.relpath(file_path, repository_path),
                )
    with open(filename, "rb") as f:
        repository = f.read()
    os.remove(filename)
    return repository


def unpack_workspace(base_dir: str, name: str, repository: bytes):
    workspace_path = os.path.join(base_dir, name)
    filepath = f".tmp.{name}"
    with open(filepath, "wb") as f:
        f.write(repository)
    unpack_archive(filepath, workspace_path, format=ARCHIVE_FORMAT)

    os.remove(filepath)

    return workspace_path


def find_package_entrypoint(file_location: str):
    """Find the first python init file in a directory.

    NOTE: this function assumes that there is a single entrypoint in a
    package. If there are multiple, it may fail to get definitions.
    """
    if not os.path.isdir(file_location):
        if file_location.endswith(".py"):
            return file_location
        msg = (
            "Entrypoint needs to be a python package or a python file, got: {}"
        ).format(file_location)
        raise ValueError(msg)

    init_file = _find_first_init_file(file_location)
    if init_file is None:
        raise ValueError(
            f"Could not find __init__.py file in directory: {file_location}"
        )
    return init_file


def _find_first_init_file(file_location):
    for root, _, files in os.walk(file_location):
        for file in files:
            if file == "__init__.py":
                return os.path.join(root, file)


def find_definitions(module_name: str, typ: type):
    module = importlib.import_module(module_name)
    context = vars(module)

    definitions = []
    for _, obj in context.items():
        if isinstance(obj, typ):
            definitions.append(obj)
    return definitions
