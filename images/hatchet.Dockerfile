ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

ARG VULKAN_HOME
ARG VULKAN_PORT
ARG VULKAN_SERVER_PATH
ARG VULKAN_SCRIPTS_PATH
ENV VULKAN_HOME=${VULKAN_HOME}
ENV VULKAN_PORT=${VULKAN_PORT}
ENV VULKAN_SERVER_PATH=${VULKAN_SERVER_PATH}
ENV VULKAN_SCRIPTS_PATH=${VULKAN_SCRIPTS_PATH}
EXPOSE ${VULKAN_PORT}

# Install basic requirements & uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential vim \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

# Build arguments for PyPI package installation
ARG USE_PYPI=false
ARG VULKAN_VERSION
ARG VULKAN_ENGINE_VERSION

# Install vulkan-hatchet-server
# Copy local files (always needed for dev builds and vulkan-hatchet which is not on PyPI)
COPY vulkan /workspace/vulkan
COPY vulkan-hatchet /workspace/vulkan-hatchet

# Conditional installation: Use PyPI packages for production builds, local copy for development
WORKDIR /workspace
RUN if [ "$USE_PYPI" = "true" ]; then \
      echo "Installing vulkanlabs-vulkan from PyPI (production build)..."; \
      uv pip install --system --no-cache "vulkanlabs-vulkan==${VULKAN_VERSION}" && \
      rm -rf /workspace/vulkan && \
      echo "Installing vulkan-hatchet from local copy..."; \
      uv pip install --system --no-cache /workspace/vulkan-hatchet; \
    else \
      echo "Using local packages (development build)..."; \
      uv pip install --system --no-cache /workspace/vulkan-hatchet; \
    fi

COPY --chmod=700 vulkan-hatchet/scripts/* ${VULKAN_SCRIPTS_PATH}/

# Run vulkan-hatchet-server
WORKDIR ${VULKAN_SCRIPTS_PATH}
CMD ["./entrypoint.sh"]