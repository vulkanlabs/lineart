ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}

EXPOSE 6001

WORKDIR /app
COPY server server/
COPY poetry.lock pyproject.toml README.md ./
RUN pip install poetry
RUN poetry install
# TODO: this creates an empty database instance
RUN poetry run python server/db.py

ENTRYPOINT ["poetry", "run",  "fastapi", "dev", "server/app.py", "--host", "0.0.0.0", "--port", "6001"]
