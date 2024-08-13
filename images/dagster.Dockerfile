ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

ARG DAGSTER_HOME
ARG DAGSTER_PORT
ENV DAGSTER_HOME=${DAGSTER_HOME}
ENV DAGSTER_PORT=${DAGSTER_PORT}
EXPOSE ${DAGSTER_PORT}

ARG VULKAN_HOME
ARG VULKAN_PORT
ENV VULKAN_HOME=${VULKAN_HOME}
ENV VULKAN_PORT=${VULKAN_PORT}
EXPOSE ${VULKAN_PORT}

RUN apt-get update && apt-get install -y --no-install-recommends \
build-essential vim \
&& rm -rf /var/lib/apt/lists/*

RUN pip install uv
RUN uv pip install --system dagster-webserver "fastapi[standard]" pyyaml pytest pytest-httpserver

COPY vulkan_dagster /tmp/vulkan_dagster
RUN uv pip install --system /tmp/vulkan_dagster && pytest /tmp/vulkan_dagster 

COPY vulkan_dagster_deploy/config/* ${DAGSTER_HOME}/
COPY vulkan_dagster_deploy/mock_workspace ${DAGSTER_HOME}/workspaces/mock_workspace
COPY vulkan_dagster_deploy/app.py ${VULKAN_HOME}/

WORKDIR /opt

RUN mkdir venvs
COPY vulkan_dagster_deploy/scripts/* ./scripts/

ENTRYPOINT ["sh", "scripts/entrypoint.sh"]