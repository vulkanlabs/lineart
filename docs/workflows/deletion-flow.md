## Workflow: Deletion Flow

This sequence shows how deletions (policies, versions, runs) are processed and cascaded safely.

### Actors and components
- Client (UI/SDK)
- API Server (`vulkan-server`)
- Engine (`vulkan-engine`)
- App DB

### High-level sequence
1. Client issues delete request for a resource (policy/version/run)
2. API validates the request and delegates to Engine
3. Engine enforces constraints (e.g., cannot delete executed version)
4. Engine performs deletion or marks for soft-delete
5. API returns status; follow-up cleanup jobs may run asynchronously

### Constraints & safeguards
- Referential integrity between policies, versions, and runs
- Soft-deletion for auditability when appropriate

### Diagram
- Source: `docs/diagrams/excalidraw/sequence-deletion.excalidraw`


