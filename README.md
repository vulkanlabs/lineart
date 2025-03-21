# Vulkan Labs Monorepo

## Setup

### Python

#### [uv](https://github.com/astral-sh/uv)

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

### Configuration

You need to set some basic configuration values.
Choose the "local" config option.

```bash
make pull-config
make config
```

### Frontend

1. npm: We use npm as our TS package manager. We recommend installing [`nvm`](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating) and using it to install Node >= 22 and npm version >=10
2. Linting, formatting, etc: let the default config do it for you.


### [OpenAPI Generator](https://github.com/OpenAPITools/openapi-generator?tab=readme-ov-file)

We use `openapi-generator` to generate TypeScript models of our backend APIs.
To install it, the recommended path is:

1. Install OpenJDK (pre-requisite) 
2. Install `openapi-generator` via npm:
   1. `npm install @openapitools/openapi-generator-cli -g`