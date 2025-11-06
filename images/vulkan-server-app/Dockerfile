ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

# Build arguments for PyPI package installation
ARG USE_PYPI=false
ARG VULKAN_VERSION
ARG VULKAN_ENGINE_VERSION

EXPOSE 6001

WORKDIR /app

RUN pip install uv
RUN uv pip install --system --no-cache sqlalchemy psycopg2

# Copy local files (always needed for dev builds and vulkan-server which is not on PyPI)
COPY vulkan vulkan
COPY vulkan-engine vulkan-engine
COPY vulkan-server vulkan-server

# Conditional installation: Use PyPI packages for production builds, local copy for development
RUN if [ "$USE_PYPI" = "true" ]; then \
      echo "Installing vulkanlabs-vulkan and vulkanlabs-vulkan-engine from PyPI (production build)..."; \
      uv pip install --system --no-cache \
        "vulkanlabs-vulkan==${VULKAN_VERSION}" \
        "vulkanlabs-vulkan-engine==${VULKAN_ENGINE_VERSION}" && \
      rm -rf vulkan vulkan-engine && \
      echo "Installing vulkan-server from local copy..."; \
      uv pip install --system --no-cache ./vulkan-server; \
    else \
      echo "Using local packages (development build)..."; \
      uv pip install --system --no-cache ./vulkan ./vulkan-engine ./vulkan-server; \
    fi


COPY --chmod=700 images/vulkan-server-app/app.sh .
CMD ["/app/app.sh"]
