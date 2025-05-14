# Vulkan

[![Discord](https://img.shields.io/badge/Discord-Vulkan%20Labs-5865F2.svg?logo=discord)](https://discord.gg/sRf66v8D)

A complete policy design and orchestration framework.

## Getting Started

### Pre-requisites

- make
- uv: [Installation Guide](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)
- Docker: [Installation Guide](https://docs.docker.com/get-started/get-docker/)
- git: [Installation Guide](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- Node: [Installation Guide](https://nodejs.org/en/download)
  - Select the option that matches your operating system
  - Use any selection in the middle option (we reccomend nvm for developers)
  - Choose "with npm" at the last option (default)

#### Installing `make`

We use the `make` command to install and manage the application. Install it using one of the following options, depending on your OS:

##### Linux (Ubuntu/Debian)

```
sudo apt install make
```

##### macOS

```
brew install make
```

### Setting Up

1. Cloning the repository
```
git clone https://github.com/vulkanlabs/lineart.git
```
2. Navigate to the directory:
```
cd lineart
```
3. Create the basic configuration
```
# Select the "local" option when prompted
make config
```
4. Run everything
```
make run
``` 

## Contributing

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
make config
```

#### Pre-Commit

Pre-commit hooks are already configured in the repo.
Activate them by running

```bash
uv run pre-commit install
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

### Continuous Integration

#### Common Actions

Check out our Makefile for common actions.
A simple `make build up` will get you running.

#### GitHub Actions + act

This section is useful when developing the CI itself.
For day-to-day usage, see above.

This project uses GitHub Actions for CI.
Follow the steps below to be able to run these locally with [Act](https://github.com/nektos/act).

1. Ensure you have Docker installed
2. Install using the [appropriate method](https://nektosact.com/installation/index.html)   
3. (M-series Macs) Create an alias: `alias act="act --container-architecture=linux/amd64"`
4. Run `act`
   - If asked, choose the "Medium" sized image