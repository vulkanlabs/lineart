ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

EXPOSE 6001

WORKDIR /app

RUN pip install uv
RUN uv pip install --system --no-cache sqlalchemy psycopg2

# Copy and install packages in dependency order
COPY vulkan vulkan/
COPY vulkan-engine vulkan-engine/
COPY vulkan-server vulkan-server/
RUN uv pip install --system --no-cache vulkan/ vulkan-engine/ vulkan-server/

COPY --chmod=700 images/vulkan-server-app/app.sh .
CMD ["/app/app.sh"]
