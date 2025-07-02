"""Utilities for loading prompts from the prompts directory."""

import os
from pathlib import Path
from typing import Optional

import jinja2


def load_prompt(prompt_name: str, prompts_dir: Optional[str] = None) -> str:
    """Load a prompt from the prompts directory.

    Args:
        prompt_name: Name of the prompt file (with or without .md extension)
        prompts_dir: Path to prompts directory. If None, uses VULKAN_PROMPTS_PATH env var.

    Returns:
        Content of the prompt file

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    if prompts_dir is None:
        prompts_dir = os.getenv("VULKAN_PROMPTS_PATH", "/app/prompts")

    prompts_path = Path(prompts_dir)

    if not prompts_path.exists():
        raise FileNotFoundError(f"Prompts directory not found: {prompts_path}")

    # Add .md extension if not present
    if not prompt_name.endswith(".md"):
        prompt_name += ".md"

    prompt_path = prompts_path / prompt_name

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def load_jinja_template(template_name: str, **kwargs) -> str:
    """Load and render a jinja2 template from the prompts/templates directory.

    Args:
        template_name: Name of the template file (with or without .md.j2 extension)
        **kwargs: Variables to pass to the template

    Returns:
        Rendered template content

    Raises:
        FileNotFoundError: If the template file doesn't exist
    """
    # Default to the prompts directory relative to this file's location
    default_prompts_dir = Path(__file__).parent.parent / "prompts"
    prompts_dir = os.getenv("VULKAN_PROMPTS_PATH", str(default_prompts_dir))
    templates_dir = Path(prompts_dir) / "templates"

    if not templates_dir.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    # Add .md.j2 extension if not present
    if not template_name.endswith(".md.j2"):
        template_name += ".md.j2"

    template_path = templates_dir / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    # Load and render template
    template_loader = jinja2.FileSystemLoader(templates_dir)
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template(template_name)

    return template.render(**kwargs)


def get_base_system_prompt() -> str:
    """Get the base system prompt for the Vulkan agent.

    Returns:
        Base system prompt content
    """
    return load_prompt("base-system-prompt")
