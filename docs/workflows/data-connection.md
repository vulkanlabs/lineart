## Workflow: Data Connection Lifecycle

This sequence shows how data connections are created, validated, and used by policies.

### Actors and components
- Client (UI/SDK)
- API Server (`vulkan-server`)
- Engine (`vulkan-engine`)
- External Data Source
- App DB

### High-level sequence
1. Client creates/updates a data connection via API (credentials, endpoints, metadata)
2. API validates payload and stores connection via Engine
3. Engine validates connectivity (where supported) and persists config
4. Policies reference the data connection during execution
5. Engine accesses the external system using stored config during runs

### Diagram
- Source: `docs/diagrams/excalidraw/sequence-data-connection.excalidraw`

### Notes
- Sensitive fields should be handled via env/secrets where possible
- Connection validation may be synchronous on create/update or deferred to first use


