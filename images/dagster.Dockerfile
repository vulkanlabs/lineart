ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

# ARG APP_PORT=6000
# COPY scripts scripts/
# COPY server server/

ARG DAGSTER_HOME
ENV DAGSTER_HOME=${DAGSTER_HOME}

ARG TEST_DATA_SERVER_PORT=5000
ARG TEST_CLIENT_SERVER_PORT=5001
ENV TEST_DATA_SERVER_PORT=${TEST_DATA_SERVER_PORT}
ENV TEST_CLIENT_SERVER_PORT=${TEST_CLIENT_SERVER_PORT}


WORKDIR ${DAGSTER_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install dagster-webserver

# TODO: import only user code here
# COPY poetry.lock pyproject.toml README.md ./
COPY vulkan_dagster vulkan_dagster/
# RUN poetry install --no-root

EXPOSE 3000
COPY config/workspace.yaml config/dagster.yaml ${DAGSTER_HOME}/

ENTRYPOINT ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]