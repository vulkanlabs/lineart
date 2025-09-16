ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION}

WORKDIR /app
COPY images/test-data-server/resources/* ./
COPY images/test-data-server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["fastapi", "dev", "app.py", "--host", "0.0.0.0", "--port", "5000"]
