from vulkan.spec.dependency import Dependency


def normalize_node_id(node_id: str) -> str:
    return node_id.replace(".", "_")


def normalize_dependencies(
    dependencies: dict[str, Dependency],
) -> dict[str, Dependency]:
    return {normalize_node_id(k): v for k, v in dependencies.items()}
