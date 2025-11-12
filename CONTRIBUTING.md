
# Contributing

## Pre-Requisites

- make
- Docker: [Installation Guide](https://docs.docker.com/get-started/get-docker/)
- uv: [Installation Guide](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
- git: [Installation Guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Node: [Installation Guide](https://nodejs.org/en/download)
  - Select the option that matches your operating system
  - Use any selection in the middle option (we reccomend nvm for developers)
  - Choose "with npm" at the last option (default)

## Building the images

We have two separate `docker-compose` files.

- `docker-compose.yaml`: Uses pre-built images from our GitHub repository.
- `docker-compose.dev.yaml`: Builds all images locally. Requires a more complete environment.

To use the complete setup, we need to override the default compose file.
Add the following line to your `.bashrc` or equivalent.

```sh
export COMPOSE_FILE="docker-compose.yaml:docker-compose.dev.yaml"
```

## Python

### [uv](https://github.com/astral-sh/uv)

We use `uv` as our Python package manager.
The root of the project is a package defined using uv's concept of workspaces.
You should be able to run `uv sync` once at the root level and have everything set up for you.

Just run:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Setup the package
uv sync
```

### Database Migrations

We use Alembic for database migrations with sequential numbering.

To create a new migration:

```bash
# First, check the latest migration number in vulkan-engine/vulkan_engine/alembic/versions/
# Then create the next sequential migration
#
# IMPORTANT: review the variables below to ensure they point to your dev database.
# DB_USER
# DB_PASSWORD
# DB_DATABASE
# DB_HOST
# DB_PORT
#
cd vulkan-engine
uv run alembic revision --autogenerate --rev-id="003" -m "description_of_your_changes" 
```

**Important:**
- Use zero-padded sequential numbers (001, 002, 003, etc.)
- Replace the rev-id with the next number in sequence
- Use descriptive, snake_case names for the migration description
- Example: `uv run alembic revision --rev-id="003" -m "add_user_authentication"`

This will generate a file like: `003_add_user_authentication.py`

## Configuration

You need to set some basic configuration values.
Choose the "local" config option.

```bash
make config
```

### Pre-Commit

Pre-commit hooks are already configured in the repo.
Activate them by running

```bash
uv run pre-commit install
```

## Frontend

1. npm: We use npm as our TS package manager. We recommend installing [`nvm`](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) and using it to install Node >= 22 and npm version >=10
2. Linting, formatting, etc: let the default config do it for you.

## [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator?tab=readme-ov-file)

We use `openapi-generator` to generate TypeScript models of our backend APIs.
To install it, the recommended path is:

1. Install OpenJDK (pre-requisite)
2. Install `openapi-generator` via npm:
   1. `npm install @openapitools/openapi-generator-cli -g`

## Continuous Integration

### Common Actions

Check out our Makefile for common actions.
A simple `make build up` will get you running.

### GitHub Actions + act

This section is useful when developing the CI itself.
For day-to-day usage, see above.

This project uses GitHub Actions for CI.
Follow the steps below to be able to run these locally with [Act](https://github.com/nektos/act).

1. Ensure you have Docker installed
2. Install using the [appropriate method](https://nektosact.com/installation/index.html)
3. (M-series Macs) Create an alias: `alias act="act --container-architecture=linux/amd64"`
4. Run `act`
   - If asked, choose the "Medium" sized image
