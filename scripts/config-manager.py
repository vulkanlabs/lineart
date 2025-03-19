import os
import shutil

import click
import dotenv
import questionary

ENVS = ["local", "dev", "prod"]
PROMPT = "Select the environment to activate"


def _try_get_active_env():
    try:
        with open("config/active_env", "r") as f:
            env = f.read().strip()
    except FileNotFoundError:
        return None

    if env in ENVS:
        return env
    return None


def _get_env_status(envs: list[str]):
    env_status = {env: False for env in envs}
    active_env = _try_get_active_env()
    if active_env:
        env_status[active_env] = True
    return env_status


@click.command()
def cli():
    env_status = _get_env_status(ENVS)
    choices = []
    for env, active in env_status.items():
        suffix = " (active)" if active else ""
        choice = questionary.Choice(env + suffix, value=env, checked=active)
        choices.append(choice)
    answer = questionary.select(PROMPT, choices=choices, show_selected=True).ask()

    if os.path.exists("config/active_env"):
        shutil.copy("config/active_env", "config/active_env.bak")

    if os.path.exists("config/active"):
        shutil.rmtree("config/active")

    shutil.copy("config/local/.env", "frontend/.env.local")
    shutil.copytree(f"config/{answer}/", "config/active/", dirs_exist_ok=True)
    shutil.copy("config/active/.env", ".env")
    with open("config/active_env", "w") as f:
        f.write(answer)
    dotenv.load_dotenv("config/active/.env", override=True)

    if os.path.exists("config/active_env.bak"):
        os.unlink("config/active_env.bak")
    click.echo(f"{answer} activated")


if __name__ == "__main__":
    cli()
