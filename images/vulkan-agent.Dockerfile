ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

# Build arguments for customization
ARG APP_PORT=8001
ARG DOCS_PATH=/app/docs
ARG DATA_PATH=/app/data

EXPOSE ${APP_PORT}

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy the vulkan-agent source code
COPY vulkan-agent vulkan-agent/

# Copy documentation for knowledge base to the configured docs path
COPY docs ${DOCS_PATH}

# Create a non-root user for security
RUN groupadd -r vulkan && useradd -r -g vulkan vulkan

# Create data directory for the database and ensure proper permissions
RUN mkdir -p ${DATA_PATH} && chown -R vulkan:vulkan ${DATA_PATH}

# Install the vulkan-agent package and its dependencies as root to avoid permission issues
RUN uv pip install --system --no-cache vulkan-agent/

# Change ownership of the entire app directory to vulkan user
RUN chown -R vulkan:vulkan /app

# Also ensure vulkan user has access to Python site-packages if needed
RUN chown -R vulkan:vulkan /usr/local/lib/python3.12/site-packages/

USER vulkan

# Health check (using the configured port from ARG)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT}/health || exit 1

# Start the FastAPI application
# Host and port will be read from environment variables or use defaults
CMD ["sh", "-c", "uvicorn vulkan_agent.app:app --host ${HOST:-0.0.0.0} --port ${PORT:-8001}"]
