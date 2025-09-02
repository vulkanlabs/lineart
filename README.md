# Vulkan

[![Discord](https://img.shields.io/badge/Discord-Vulkan%20Labs-5865F2.svg?logo=discord)](https://discord.gg/2tAYKfJynV)
[![license](https://img.shields.io/badge/License-Apache_2.0-green)](https://github.com/vulkanlabs/lineart/blob/master/LICENSE)

A complete workflow design and orchestration framework.

## Getting Started

1. Sign Up on `engine.vulkan.software`
2. Install the vulkan package
   1. `git clone https://github.com/vulkanlabs/lineart.git`
   2. `cd lineart`
   3. `uv sync` 
3. Log in using the command line: `vcli login`
4. Select a project to use: `vcli projects set`

## Running Locally

### Pre-requisites

- make
- Docker: [Installation Guide](https://docs.docker.com/get-started/get-docker/)

### Setting Up

1. Cloning the repository

```
git clone https://github.com/vulkanlabs/lineart.git
```

2. Run: The app will be available at port 3003

```
cd lineart
make run
```

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

### Tutorial and Documentation

We have a [short tutorial](docs/how-to/) and [example notebooks](vulkan/docs/notebooks) to get you started!

More detailed documentation coming soon.

## Project Structure

Below is an overview of the main folders and their purpose:

### `vulkan`

Core library code that implements the policy design and orchestration framework. Contains the main business logic and models.

This is the best place to start exploring the code.

### `frontend`

Contains the web-based user interface built with TypeScript and React. This is where client-side code resides.

### `vulkan-server`

API server implementation that exposes the core functionality as RESTful endpoints. This is the backend that the frontend communicates with.

### `vulkan-dagster`

Integration with Dagster workflow engine for defining and executing data pipelines and policy workflows.
