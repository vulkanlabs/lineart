"""Simplified documentation loader for Vulkan documentation."""

import os
from pathlib import Path
from typing import Optional


class DocumentationLoader:
    """Loads all Vulkan documentation into a single string for LLM context."""

    def __init__(self, docs_path: Optional[str] = None):
        """Initialize the documentation loader.

        Args:
            docs_path: Path to the documentation directory. If None, uses VULKAN_DOCS_PATH env var.
        """
        self.docs_path = Path(docs_path or os.getenv("VULKAN_DOCS_PATH", "/docs"))
        self._cached_docs: Optional[str] = None

    def load_documentation(self) -> str:
        """Load all documentation files into a single string.

        Returns:
            Combined documentation content as a single string.
        """
        if self._cached_docs is not None:
            return self._cached_docs

        if not self.docs_path.exists():
            print(f"Warning: Documentation path {self.docs_path} does not exist")
            return ""

        docs_content = []

        # Recursively find all markdown files
        for md_file in self.docs_path.rglob("*.md"):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Add file header for context
                    relative_path = md_file.relative_to(self.docs_path)
                    docs_content.append(
                        f"# File: {relative_path}\n\n{content}\n\n---\n"
                    )
            except Exception as e:
                print(f"Warning: Could not read file {md_file}: {e}")

        # Cache the result
        self._cached_docs = "\n".join(docs_content)
        return self._cached_docs

    def get_documentation_context(self) -> str:
        """Get documentation formatted for LLM context.

        Returns:
            Documentation formatted as context for the LLM.
        """
        docs = self.load_documentation()
        if not docs:
            return ""

        return f"""
## Vulkan Platform Documentation

The following documentation provides comprehensive information about the Vulkan platform, including how to manage policies, data sources, and other platform features:

{docs}

Use this documentation to answer questions about Vulkan platform capabilities, configuration, and best practices.
"""

    def reload_documentation(self) -> str:
        """Force reload documentation from disk, clearing cache.

        Returns:
            Combined documentation content as a single string.
        """
        self._cached_docs = None
        return self.load_documentation()

    def update_documentation_file(self, relative_path: str, content: str) -> None:
        """Update or create a documentation file.

        Args:
            relative_path: Path relative to docs directory (e.g., "how-to/new-feature.md")
            content: File content to write
        """
        file_path = self.docs_path / relative_path

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Clear cache to force reload on next access
        self._cached_docs = None
        print(f"Updated documentation file: {relative_path}")

    def delete_documentation_file(self, relative_path: str) -> None:
        """Delete a documentation file.

        Args:
            relative_path: Path relative to docs directory
        """
        file_path = self.docs_path / relative_path
        if file_path.exists():
            file_path.unlink()
            # Clear cache to force reload on next access
            self._cached_docs = None
            print(f"Deleted documentation file: {relative_path}")
        else:
            print(f"File not found: {relative_path}")

    def list_documentation_files(self) -> list[str]:
        """List all documentation files.

        Returns:
            List of relative paths to documentation files.
        """
        if not self.docs_path.exists():
            return []

        files = []
        for md_file in self.docs_path.rglob("*.md"):
            relative_path = md_file.relative_to(self.docs_path)
            files.append(str(relative_path))

        return sorted(files)


# Global instance for reuse
_documentation_loader: Optional[DocumentationLoader] = None


def get_documentation_loader() -> DocumentationLoader:
    """Get the global documentation loader instance."""
    global _documentation_loader
    if _documentation_loader is None:
        _documentation_loader = DocumentationLoader()
    return _documentation_loader


def create_system_prompt_with_docs(base_prompt: str) -> str:
    """Create a system prompt that includes the documentation context.

    Args:
        base_prompt: The base system prompt for the agent.

    Returns:
        Enhanced system prompt with documentation context.
    """
    loader = get_documentation_loader()
    docs_context = loader.get_documentation_context()

    if not docs_context:
        return base_prompt

    return f"""{base_prompt}

{docs_context}"""


def refresh_documentation_loader() -> None:
    """Refresh the global documentation loader instance."""
    global _documentation_loader
    if _documentation_loader is not None:
        _documentation_loader.reload_documentation()


def clear_documentation_cache() -> None:
    """Clear the documentation cache, forcing a reload on next access."""
    global _documentation_loader
    if _documentation_loader is not None:
        _documentation_loader._cached_docs = None
