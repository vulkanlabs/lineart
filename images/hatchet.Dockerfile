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

# Install vulkan-hatchet-server
COPY vulkan ${VULKAN_SERVER_PATH}/vulkan
COPY vulkan-hatchet ${VULKAN_SERVER_PATH}/vulkan-hatchet
RUN uv pip install --system --no-cache ${VULKAN_SERVER_PATH}/vulkan-hatchet

COPY --chmod=700 vulkan-hatchet/scripts/* ${VULKAN_SCRIPTS_PATH}/

# Run vulkan-hatchet-server
WORKDIR ${VULKAN_SCRIPTS_PATH}
CMD ["./entrypoint.sh"]