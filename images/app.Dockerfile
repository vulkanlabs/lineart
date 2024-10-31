ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

EXPOSE 6001

WORKDIR /app

RUN pip install uv
RUN uv pip install --system sqlalchemy psycopg2

# TODO: make this dependency explicit to the vulkan package
COPY vulkan-public vulkan-public
COPY vulkan vulkan
RUN uv pip install --system vulkan

COPY vulkan-server vulkan-server/
RUN uv pip install --system vulkan-server/

COPY images/app.sh .
ENTRYPOINT ["bash", "/app/app.sh"]
