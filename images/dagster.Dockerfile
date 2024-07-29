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

ARG TEST_DATA_SERVER_PORT=5000
ARG TEST_CLIENT_SERVER_PORT=5001
ENV TEST_DATA_SERVER_PORT=${TEST_DATA_SERVER_PORT}
ENV TEST_CLIENT_SERVER_PORT=${TEST_CLIENT_SERVER_PORT}

RUN apt-get update && apt-get install -y --no-install-recommends \
build-essential \
&& rm -rf /var/lib/apt/lists/*

# RUN pip install dagster-webserver
RUN pip install poetry

COPY vulkan_dagster /tmp/vulkan_dagster
COPY vulkan_dagster_deploy/config/* ${DAGSTER_HOME}/
COPY vulkan_dagster_deploy/mock_workspace ${DAGSTER_HOME}/workspaces/mock_workspace
COPY vulkan_dagster_deploy/app.py ${VULKAN_HOME}/

WORKDIR /opt

COPY vulkan_dagster_deploy/entrypoint.sh ./
COPY vulkan_dagster_deploy/pyproject.toml ./

RUN poetry install
RUN poetry add /tmp/vulkan_dagster

# WORKDIR /opt/vulkan_dagster

# RUN poetry install
# RUN poetry build -f wheel
# RUN pip install dist/vulkan_dagster-0.1.0-py3-none-any.whl

ENTRYPOINT ["sh", "entrypoint.sh"]