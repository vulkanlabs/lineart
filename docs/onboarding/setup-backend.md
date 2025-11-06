## Backend Setup Guide

This guide gets the backend running locally with Docker and the provided configs.

### Prerequisites
- Docker and Docker Compose
- Python 3.12 and `uv` (`pipx install uv`), for scripts and local tooling
- Make (optional but recommended)

### 1) Clone and enter the repo

```bash
git clone <your-fork-or-origin> lineart && cd lineart
```

### 2) Activate a local config
Choose one of the following:

- Using Make (non‑interactive):

```bash
make config
```

- Using the interactive config manager:

```bash
uv run python scripts/config-manager.py
```

This writes `config/active/*` and a project `.env`. The main env files used by services are under `config/active/` (e.g., `app.env`, `app-db.env`, `dagster.env`, `dagster-db.env`, `hatchet.env`, `.env`).

### 3) Start backend services (development stack)

Use the dev compose file to build from local sources:

```bash
docker-compose -f docker-compose.dev.yaml up -d --build
```

Services (dev):
- API server (`app`) FastAPI on http://localhost:6001
- Dagster UI on http://localhost:3000
- Test Data server on http://localhost:5001
- Postgres instances for app and Dagster (internal)

Follow logs:

```bash
docker-compose -f docker-compose.dev.yaml logs -f app dagster testdata
```

Stop stack and remove volumes when needed:

```bash
docker-compose -f docker-compose.dev.yaml down -v --remove-orphans
```

### 4) Verify API is up

```bash
curl http://localhost:6001/docs
```

You should see the FastAPI Swagger UI at `/docs` in a browser.

### 5) Useful Make targets

```bash
# Lint/format Python (ruff) and format frontend
make lint

# Bring up the default compose stack (non-dev)
make run

# Tear down containers and remove volumes
make down

# Regenerate OpenAPI client for the frontend
make openapi
```

### 6) Notes on databases and migrations
- The app and Dagster databases are created from the compose files and initialized on first run.
- Engine migrations live under `vulkan_engine/alembic` and are applied by the backend services during startup or release workflows.

### 7) Local Python tooling (optional)
If you want to run scripts or tests locally without containers:

```bash
uv sync
uv run pytest -sv --tb=short --disable-warnings -m "not integration"
```

### 8) Common troubleshooting
- If services fail to read envs, re-run `make config` to refresh `config/active` and `.env`.
- Clear local volumes if Postgres migrations drift: `docker volume ls` then `docker volume rm <name>` for the project volumes.
- Check container logs for startup errors: `docker-compose -f docker-compose.dev.yaml logs -f app`.


