ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

EXPOSE 8001

WORKDIR /app

# Install uv for fast dependency management
RUN pip install uv

# Copy the vulkan-agent source code
COPY vulkan-agent vulkan-agent/

# Install the vulkan-agent package and its dependencies
RUN uv pip install --system --no-cache vulkan-agent/

# Create a non-root user for security
RUN groupadd -r vulkan && useradd -r -g vulkan vulkan
RUN chown -R vulkan:vulkan /app
USER vulkan

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start the FastAPI application
CMD ["python", "-m", "vulkan_agent.app"]
