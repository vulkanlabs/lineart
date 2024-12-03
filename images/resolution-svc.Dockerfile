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

RUN pip install uv

# Install resolution-svc
COPY vulkan-public ${VULKAN_SERVER_PATH}/vulkan-public
COPY vulkan ${VULKAN_SERVER_PATH}/vulkan

COPY resolution-svc ${VULKAN_SERVER_PATH}/resolution-svc
RUN uv pip install --system --no-cache ${VULKAN_SERVER_PATH}/resolution-svc

RUN mkdir ${VULKAN_VENVS_PATH}
COPY resolution-svc/scripts/* ${VULKAN_SCRIPTS_PATH}/

# Run server
WORKDIR ${VULKAN_SERVER_PATH}
ENTRYPOINT ["fastapi", "dev", "./resolution-svc/resolution_svc/app.py", "--host", "0.0.0.0", "--port", "8080", "--no-reload"]
