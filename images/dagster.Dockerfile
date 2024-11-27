ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

ARG DAGSTER_HOME
ARG DAGSTER_PORT
ENV DAGSTER_HOME=${DAGSTER_HOME}
ENV DAGSTER_PORT=${DAGSTER_PORT}
EXPOSE ${DAGSTER_PORT}

ARG VULKAN_HOME
ARG VULKAN_PORT
ARG VULKAN_SERVER_PATH
ARG VULKAN_SCRIPTS_PATH
ARG VULKAN_VENVS_PATH
ENV VULKAN_HOME=${VULKAN_HOME}
ENV VULKAN_PORT=${VULKAN_PORT}
ENV VULKAN_SERVER_PATH=${VULKAN_SERVER_PATH}
ENV VULKAN_SCRIPTS_PATH=${VULKAN_SCRIPTS_PATH}
ENV VULKAN_VENVS_PATH=${VULKAN_VENVS_PATH}
EXPOSE ${VULKAN_PORT}

# Install Dagster webserver + vulkan core library
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential vim \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

# Install vulkan-dagster-server
COPY vulkan-public ${VULKAN_SERVER_PATH}/vulkan-public
COPY vulkan ${VULKAN_SERVER_PATH}/vulkan
COPY vulkan-dagster ${VULKAN_SERVER_PATH}/vulkan-dagster
RUN uv pip install --system --no-cache ${VULKAN_SERVER_PATH}/vulkan-dagster

COPY vulkan-dagster/config/dagster.yaml ${DAGSTER_HOME}/
COPY vulkan-dagster/config/workspace.yaml ${VULKAN_HOME}/
COPY vulkan-dagster/mock_workspace ${VULKAN_HOME}/workspaces/mock_workspace

RUN mkdir ${VULKAN_VENVS_PATH}
COPY --chmod=700 vulkan-dagster/scripts/* ${VULKAN_SCRIPTS_PATH}/

# Run both servers
WORKDIR ${VULKAN_SCRIPTS_PATH}
CMD ["./entrypoint.sh"]