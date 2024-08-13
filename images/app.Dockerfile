ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

EXPOSE 6001

RUN pip install uv
RUN uv pip install --system "fastapi[standard]" sqlalchemy requests python-dotenv pydantic dagster-graphql pytest pytest-httpserver

COPY vulkan_dagster /tmp/vulkan_dagster
RUN uv pip install --system /tmp/vulkan_dagster

WORKDIR /app
COPY server server/
# TODO: this creates an empty database instance
RUN python server/db.py

ENTRYPOINT ["fastapi", "dev", "server/app.py", "--host", "0.0.0.0", "--port", "6001"]
