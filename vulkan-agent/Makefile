.PHONY: help test test-integration test-all lint format clean clean-db clean-all install integration-demo

# Default target
help:
	@echo "Available commands:"
	@echo "  test            Run unit tests (fast feedback)"
	@echo "  test-integration Run integration tests only"
	@echo "  test-all        Run all tests (unit + integration)"
	@echo "  lint            Run code linting and formatting checks"
	@echo "  format          Format code with ruff"
	@echo "  clean           Clean up cache files and build artifacts"
	@echo "  clean-db        Clean up database files"
	@echo "  clean-all       Clean up everything (cache + database files)"
	@echo "  install         Install dependencies"
	@echo "  integration-demo Run integration test as standalone demo"

# Fast unit tests for quick feedback during development
test:
	uv run pytest test/ --ignore=test/integration -v
	@$(MAKE) clean-db

# Run only integration tests
test-integration:
	uv run pytest test/integration/ -v
	@$(MAKE) clean-db

# Run all tests
test-all:
	uv run pytest test/ -v
	@$(MAKE) clean-db

# Linting and formatting
lint:
	uv run ruff check .
	uv run ruff format --check .

# Format code
format:
	uv run ruff format .

# Clean up cache and build artifacts
clean:
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +

# Clean up database files
clean-db:
	@echo "Cleaning up database files..."
	find . -name "*.db" -type f -delete
	find . -name "*.db-*" -type f -delete
	@echo "Database files cleaned up."

# Clean up everything (cache + database files)
clean-all: clean clean-db
	@echo "All cleanup completed."

# Install dependencies
install:
	uv sync

# Run the integration test as a standalone script
integration-demo:
	uv run python test/integration/test_langchain_integration.py
	@$(MAKE) clean-db
