ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

EXPOSE 8080
WORKDIR /app

RUN pip install uv

COPY vulkan-public vulkan-public
COPY vulkan vulkan
COPY upload-svc upload-svc/
RUN uv pip install --system upload-svc/

ENTRYPOINT ["fastapi", "dev" , "upload-svc/upload_svc/app.py", "--host", "0.0.0.0", "--port", "8080"]
