ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

WORKDIR /app
COPY test/resources/data_server.py server.py
RUN pip install flask

ENTRYPOINT ["flask", "--app", "server.py", "run", "--host", "0.0.0.0", "--port", "5000"]
