ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

ARG VULKAN_SERVER_DB_PATH
ENV VULKAN_SERVER_DB_PATH=${VULKAN_SERVER_DB_PATH}

EXPOSE 6001

WORKDIR /app

RUN pip install uv

# TODO: make this dependency explicit to the vulkan package
COPY vulkan /tmp/vulkan
RUN uv pip install --system /tmp/vulkan

COPY vulkan-server vulkan-server/
RUN uv pip install --system vulkan-server/
# TODO: this creates an empty database instance
RUN python vulkan-server/vulkan_server/db.py

ENTRYPOINT ["fastapi", "dev", "vulkan-server/vulkan_server/app.py", "--host", "0.0.0.0", "--port", "6001"]
