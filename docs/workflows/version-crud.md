## Workflow: Policy Version CRUD

This sequence shows how policy versions are created, listed, updated, and deleted.

### Actors and components
- Client (UI/SDK)
- API Server (`vulkan-server`)
- Engine (`vulkan-engine`)
- App DB

### High-level sequence
1. Create: Client posts a new policy version (definition, metadata)
2. Read: Client lists versions or fetches a specific one
3. Update: Client updates mutable fields (if allowed)
4. Delete: Client deletes a version (subject to constraints)

### Rules of thumb
- Enforce immutability for executed versions; allow patching drafts only
- Validate graph structure and referenced data connections

### Diagram
- Source: `docs/diagrams/excalidraw/sequence-version-crud.excalidraw`


