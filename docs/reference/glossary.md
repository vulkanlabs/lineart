## Glossary (Backend)

- Policy: Declarative definition of a data processing workflow composed of nodes
- Policy Version: Immutable snapshot of a policy definition used for execution
- Node: A step in a policy graph (e.g., allocation, branch)
- Run: An execution instance of a policy version with status and logs
- Data Connection: Configuration describing access to an external data source
- Orchestrator: External service executing jobs (Dagster or Hatchet)
- Engine: Core backend logic implementing policies and runs
- API Server: FastAPI service exposing the backend REST API
- App DB: Postgres database storing backend state
- Dagster DB: Postgres database storing orchestrator state


