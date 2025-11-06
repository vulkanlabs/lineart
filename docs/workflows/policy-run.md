## Workflow: Policy Run Lifecycle

This sequence shows how a policy run is created, executed, and reported.

### Actors and components
- Client (UI/SDK)
- API Server (`vulkan-server`)
- Engine (`vulkan-engine`)
- Orchestrator (Dagster/Hatchet)
- App DB

### High-level sequence
1. Client requests a run of a specific policy version
2. API validates request and delegates to Engine
3. Engine persists run metadata and schedules execution
4. Orchestrator executes tasks for each node in the policy graph
5. Engine records progress and final result
6. API exposes run status and logs to client

### Diagram
Add the sequence diagram (Excalidraw) illustrating API ⇄ Engine ⇄ Orchestrator interactions:
- Source: `docs/diagrams/excalidraw/sequence-policy-run.excalidraw`
- Export: `docs/diagrams/export/sequence-policy-run.png`

### Notes
- Failures should surface as structured errors from Engine, returned via FastAPI handlers
- Long-running steps are orchestrated; polling or callbacks update run status


