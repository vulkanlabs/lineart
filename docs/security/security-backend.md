## Backend Security & Secrets

### Environments and secrets
- Active env files live under `config/active/` and are copied from environment presets (`config/local`, `config/dev`, `config/prod`).
- Use `make config` or `uv run python scripts/config-manager.py` to switch environments locally.
- Never commit real secrets; the repo contains templates only. Keep sensitive values in your local `config/<env>/*.env`.

### Compose-managed environment
- Services load envs via `env_file` in the compose files (`docker-compose*.yaml`).
- Ensure `.env` at the repo root is in sync with `config/active/.env` (the setup step does this).

### Tokens and auth
- API authentication and authorization live in the server and engine layers; store tokens in env files and pass them through Compose.
- Prefer scoped tokens and least privilege for any external integrations.

### Data connections
- Store credentials in envs or secret stores; avoid plaintext in policy definitions.
- Validate and rotate credentials regularly.

### Local development hygiene
- Rotate local DBs by removing volumes when needed (`docker volume rm ...`).
- Do not reuse production credentials in local environments.


