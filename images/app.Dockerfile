ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

EXPOSE 6001

WORKDIR /app

RUN pip install uv
RUN uv pip install --system sqlalchemy psycopg2

# TODO: make this dependency explicit to the vulkan package
COPY vulkan /tmp/vulkan
RUN uv pip install --system /tmp/vulkan

COPY vulkan-server vulkan-server/
RUN uv pip install --system vulkan-server/

COPY images/app.sh .
ENTRYPOINT ["bash", "/app/app.sh"]
