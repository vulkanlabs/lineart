from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader


@dataclass
class PackageSpec:
    name: str
    path: str


def render_dockerfile(
    base_dir: str, policy: PackageSpec, dependencies: list[PackageSpec], **kwargs
):
    env = Environment(
        loader=FileSystemLoader(f"{base_dir}/resolution-svc/resolution_svc/templates")
    )
    dockerfile_template = env.get_template("Dockerfile.j2")

    return dockerfile_template.render(
        policy=policy, dependencies=dependencies, **kwargs
    )
