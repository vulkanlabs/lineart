## Product Overview

This project provides a policy-driven data processing and orchestration platform. Backend services expose APIs to manage policies and versions, orchestrate runs, and integrate with compute/orchestration tools.

### Core concepts
- Policy: a definition of how to process data via a graph of nodes
- Node: an operation in the policy (e.g., allocation, branching)
- Run: an execution instance of a policy version
- Data source: external system providing or receiving data

See `docs/how-to/1-policies.md` for user-facing concepts (screenshots and flows).

### Core backend services
- API server (`vulkan-server`)
  - FastAPI app exposing REST endpoints for policies, versions, runs, data connections, and auth
  - Entry: `vulkan_server/app.py`
  - Routers: `vulkan_server/routers/*`
  - Uses `vulkan_engine` for business logic and exceptions

- Engine (`vulkan-engine`)
  - Business logic, job execution interfaces, backends, migrations
  - Key areas: `vulkan_engine/backends`, `vulkan_engine/services`, `vulkan_engine/events.py`, `vulkan_engine/db.py`
  - Migrations: `vulkan_engine/alembic/`, config in `vulkan_engine/alembic.ini`

- Orchestrators
  - Dagster service: pipelines and UI (compose service `dagster`)
  - Hatchet service: background job execution (compose service `hatchet`)

- Databases
  - App DB (Postgres) for server/engine state
  - Dagster DB (Postgres) for orchestrator state

### High-level flow (backend perspective)
1. Client calls API on `vulkan-server` (FastAPI)
2. Server validates/authenticates, delegates to `vulkan_engine`
3. Engine persists state, emits events, schedules work via orchestration backend
4. Orchestrator (Dagster/Hatchet) executes jobs and reports back
5. Server exposes run status and logs over API

### SDKs and integrations
- Python SDK (`sdks/python`) and Lineart SDK (`sdks/lineart`) interact with the backend API
- OpenAPI generation for frontend client: `make openapi` (uses `scripts/export-openapi.py`)

### Where to look in code
- Server: `vulkan-server/vulkan_server/` (app, routers, dependencies)
- Engine: `vulkan-engine/vulkan_engine/` (backends, services, config, db, events)
- Orchestrators: `vulkan-dagster/` and `vulkan-hatchet/`
- Test data server: `images/test-data-server/`


