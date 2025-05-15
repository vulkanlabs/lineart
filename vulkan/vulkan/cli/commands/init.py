import os
import pathlib
import subprocess

import click
from cookiecutter.main import cookiecutter

from vulkan.cli.context import Context, pass_context


@click.command()
@click.option(
    "--output-dir",
    "-o",
    default=".",
    show_default=True,
    help="Directory to create the policy in",
)
@pass_context
def init(ctx: Context, output_dir: str):
    click.echo("Configuration for the new policy:")
    name = click.prompt("Name")
    version = click.prompt("Version", default="v0.0.1")
    description = click.prompt("Description", default="")

    dependencies = []
    add_dependencies = click.confirm(
        "Would you like to specify dependencies for the policy?", default=False
    )
    if add_dependencies:
        while True:
            dependency = click.prompt("Dependency name")
            dependencies.append(dependency)
            add_another = click.confirm("Add another dependency?", default=False)
            if not add_another:
                break
    dependencies = ",".join(dependencies)

    context = dict(
        name=name,
        version=version,
        description=description,
        dependencies=dependencies,
    )

    root = pathlib.Path(__file__).parents[2].resolve()
    template = os.path.join(root, "templates", "policy")

    cookiecutter(
        template=template,
        output_dir=output_dir,
        no_input=True,
        extra_context=context,
    )
    ctx.logger.info(f"Policy {name} created at {output_dir}")

    create_venv = click.confirm(
        "Would you like to create a virtual environment to develop the policy?",
        default=False,
    )
    if create_venv:
        policy_dir = os.path.join(output_dir, name)
        venv_path = os.path.join(policy_dir, ".venv")
        python_path = os.path.join(os.path.abspath(venv_path), "bin", "python")
        subprocess.run(["python", "-m", "venv", venv_path])
        subprocess.run(
            [python_path, "-m", "pip", "install", os.path.abspath(policy_dir)],
            cwd=output_dir,
        )
        ctx.logger.info("Virtual environment created and policy installed")
        ctx.logger.info(
            "To activate the virtual environment, run: "
            f"source {os.path.join(venv_path, 'bin', 'activate')}"
        )
