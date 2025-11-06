## Services Guide

This guide maps code to running services and shows common extension points.

### API Server (FastAPI)
- Path: `vulkan-server/vulkan_server/`
- Entry: `app.py` — creates the FastAPI app, configures CORS, includes routers, and sets exception handlers using `vulkan_engine.exceptions`.
- Routers: `vulkan_server/routers/` (e.g., `policies`, `policy_versions`, `runs`, `data`, `components`, `auth`, `internal`).
- Patterns
  - Define request/response models with Pydantic
  - Delegate business logic to `vulkan_engine` modules
  - Use consistent error mapping (see `ErrorResponse` in `app.py`)
- Local dev: compose service name `app` (port 6001 in dev compose)

### Engine
- Path: `vulkan-engine/vulkan_engine/`
- Responsibilities
  - Domain logic and orchestration integration
  - Persistence via `db.py`
  - Events and errors via `events.py`, `exceptions.py`
  - Pluggable backends in `backends/` and higher-level services in `services/`
- Migrations
  - Alembic files under `alembic/`, config in `alembic.ini`
  - Applied in service startup or release pipelines

### Orchestrators
- Dagster
  - Path: `vulkan-dagster/`
  - Compose service: `dagster` (port 3000)
  - Uses `vulkan` workspace bundled into the container; state in `dagster-db`

- Hatchet
  - Path: `vulkan-hatchet/`
  - Compose service: `hatchet`

### Supporting services
- Test Data server
  - Path: `images/test-data-server/`
  - Compose service: `testdata` (port 5001)

### Configuration
- Active envs are assembled under `config/active/` via `make config` or `scripts/config-manager.py`
- Compose files:
  - Dev (build from local): `docker-compose.dev.yaml`
  - Default (use images): `docker-compose.yaml`


