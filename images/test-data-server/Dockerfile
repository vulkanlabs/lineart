ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

WORKDIR /app
COPY images/test-data-server/resources/data_server.py server.py
RUN pip install "fastapi[standard]"

EXPOSE 5000

ENTRYPOINT ["fastapi", "dev", "server.py", "--host", "0.0.0.0", "--port", "5000"]
