ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

ARG VULKAN_HOME
ARG VULKAN_SERVER_PATH
ARG VULKAN_SCRIPTS_PATH
ARG VULKAN_VENVS_PATH
ENV VULKAN_HOME=${VULKAN_HOME}
ENV VULKAN_SERVER_PATH=${VULKAN_SERVER_PATH}
ENV VULKAN_SCRIPTS_PATH=${VULKAN_SCRIPTS_PATH}
ENV VULKAN_VENVS_PATH=${VULKAN_VENVS_PATH}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential vim \
    && rm -rf /var/lib/apt/lists/*

COPY resolution-svc/scripts/* ${VULKAN_SCRIPTS_PATH}/

RUN pip install uv

# Install resolution-svc
WORKDIR ${VULKAN_SERVER_PATH}
COPY vulkan-public vulkan-public
COPY resolution-svc resolution-svc
RUN uv pip install --system --no-cache resolution-svc/
## Use symlink installations after the initial setup to avoid duplicating
## the same packages in the container.
## Note: This has to be set after running the --no-cache installation,
##       as the two options are mutually exclusive.
ENV UV_LINK_MODE=symlink

# Run server
ENTRYPOINT ["fastapi", "dev", "./resolution-svc/resolution_svc/app.py", "--host", "0.0.0.0", "--port", "8080", "--no-reload"]
