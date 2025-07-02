"""Tests for the simplified documentation loader."""

import tempfile
from pathlib import Path

import pytest
from vulkan_agent.knowledge_base import (
    DocumentationLoader,
    create_system_prompt_with_docs,
    get_documentation_loader,
)


@pytest.fixture
def temp_docs_dir():
    """Create a temporary directory with test documentation files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        docs_path = Path(temp_dir)

        # Create some test markdown files
        (docs_path / "test1.md").write_text(
            "# Test Document 1\n\nThis is test content 1."
        )
        (docs_path / "test2.md").write_text(
            "# Test Document 2\n\nThis is test content 2."
        )

        # Create a subdirectory with more files
        subdir = docs_path / "subdir"
        subdir.mkdir()
        (subdir / "test3.md").write_text("# Test Document 3\n\nThis is test content 3.")

        yield docs_path


def test_documentation_loader_init():
    """Test DocumentationLoader initialization."""
    loader = DocumentationLoader("/test/path")
    assert loader.docs_path == Path("/test/path")
    assert loader._cached_docs is None


def test_documentation_loader_load_documentation(temp_docs_dir):
    """Test loading documentation from directory."""
    loader = DocumentationLoader(str(temp_docs_dir))
    docs = loader.load_documentation()

    # Should contain all three files
    assert "test1.md" in docs
    assert "test2.md" in docs
    assert "subdir/test3.md" in docs
    assert "Test Document 1" in docs
    assert "Test Document 2" in docs
    assert "Test Document 3" in docs


def test_documentation_loader_caching(temp_docs_dir):
    """Test that documentation is cached after first load."""
    loader = DocumentationLoader(str(temp_docs_dir))

    # First load
    docs1 = loader.load_documentation()

    # Second load should return cached version
    docs2 = loader.load_documentation()

    assert docs1 == docs2
    assert loader._cached_docs is not None


def test_documentation_loader_reload(temp_docs_dir):
    """Test reloading documentation clears cache."""
    loader = DocumentationLoader(str(temp_docs_dir))

    # First load
    docs1 = loader.load_documentation()

    # Add a new file
    (temp_docs_dir / "test4.md").write_text("# Test Document 4\n\nNew content.")

    # Reload should pick up new file
    docs2 = loader.reload_documentation()

    assert docs1 != docs2
    assert "test4.md" in docs2
    assert "Test Document 4" in docs2


def test_documentation_loader_nonexistent_path():
    """Test loading from nonexistent path."""
    loader = DocumentationLoader("/nonexistent/path")
    docs = loader.load_documentation()

    assert docs == ""


def test_documentation_loader_update_file(temp_docs_dir):
    """Test updating a documentation file."""
    loader = DocumentationLoader(str(temp_docs_dir))

    # Load initial docs to populate cache
    loader.load_documentation()

    # Update a file
    loader.update_documentation_file("new_file.md", "# New File\n\nNew content.")

    # Should clear cache
    assert loader._cached_docs is None

    # Reload should include new file
    docs2 = loader.load_documentation()
    assert "new_file.md" in docs2
    assert "New File" in docs2


def test_documentation_loader_delete_file(temp_docs_dir):
    """Test deleting a documentation file."""
    loader = DocumentationLoader(str(temp_docs_dir))

    # Load initial docs
    docs1 = loader.load_documentation()
    assert "test1.md" in docs1

    # Delete a file
    loader.delete_documentation_file("test1.md")

    # Should clear cache
    assert loader._cached_docs is None

    # Reload should not include deleted file
    docs2 = loader.load_documentation()
    assert "test1.md" not in docs2


def test_documentation_loader_list_files(temp_docs_dir):
    """Test listing documentation files."""
    loader = DocumentationLoader(str(temp_docs_dir))
    files = loader.list_documentation_files()

    assert len(files) == 3
    assert "test1.md" in files
    assert "test2.md" in files
    assert "subdir/test3.md" in files


def test_get_documentation_context(temp_docs_dir):
    """Test getting formatted documentation context."""
    loader = DocumentationLoader(str(temp_docs_dir))
    context = loader.get_documentation_context()

    assert "Vulkan Platform Documentation" in context
    assert "test1.md" in context
    assert "Test Document 1" in context


def test_create_system_prompt_with_docs(temp_docs_dir):
    """Test creating system prompt with documentation."""
    # Mock the global loader
    import vulkan_agent.knowledge_base as kb_module

    original_loader = kb_module._documentation_loader

    try:
        kb_module._documentation_loader = DocumentationLoader(str(temp_docs_dir))

        base_prompt = "You are a helpful assistant."
        enhanced_prompt = create_system_prompt_with_docs(base_prompt)

        assert base_prompt in enhanced_prompt
        assert "Vulkan Platform Documentation" in enhanced_prompt
        assert "Test Document 1" in enhanced_prompt

    finally:
        kb_module._documentation_loader = original_loader


def test_get_documentation_loader():
    """Test getting global documentation loader."""
    loader1 = get_documentation_loader()
    loader2 = get_documentation_loader()

    # Should return the same instance
    assert loader1 is loader2
