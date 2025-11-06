## Backend Architecture (C4)

This document provides a backend-only view using the C4 model: System Context and Container views, plus notes that lead into component details.

### System Context (backend only)
- Actors: Frontend apps/SDKs, Operators (engineers), External Data Sources
- System: Backend API + Engine + Orchestrators + DBs

Diagram (to be added via Excalidraw):
- Source: `docs/diagrams/excalidraw/system-context-backend.excalidraw`
- Export: `docs/diagrams/export/system-context-backend.png`

### Container View
- API Server (`vulkan-server`)
  - FastAPI, routers for policies, versions, runs, data, auth
  - Depends on `vulkan_engine` for business logic
  - Exposes OpenAPI at `/openapi.json` and UI at `/docs`

- Engine (`vulkan-engine`)
  - Business logic, persistence, events, job scheduling
  - Backends and services under `vulkan_engine/backends` and `vulkan_engine/services`
  - DB integration via `vulkan_engine/db.py`; migrations under `vulkan_engine/alembic`

- Orchestrators
  - Dagster service and DB for orchestration and UI
  - Hatchet service for background execution

- Databases
  - App DB (Postgres) for server/engine state
  - Dagster DB (Postgres) for orchestration state


