# Vulkan


## Vulkan Lib

The `vulkan` library is the main entrypoint for Vulkan functionality.\
It allows you to access all of Vulkan's functionality in a direct and flexible way.

### Installation

#### Git

You will need to clone this repository using git.
If you don't have it yet, you can install from this link: [git](https://git-scm.com/downloads).

#### Installing the Python Library

Currently, you need to install this package from source.\

```bash
git clone https://github.com/vulkanlabs/vulkan.git
cd vulkan
pip install .
```

## Technical Overview

### Defining and automating workflows

The main purpose of Vulkan is to facilitate creating, testing and scaling decision workflows.
You define a flow as a sequence of interconnected steps, each expressed as a Python function.

### Execution Environment

Each task (node) is executed in isolation, having access only to the inputs specified on its definition.
The outputs of each node are serialized, being accessible to the user or other nodes.
In this way, each node can be thought of as a function that runs on an independent,
disposable environment, but with durable results.

### Components (Reusable workflow parts)

We may want to create bits of logic that are shared between workflows - think data cleaning, validation.

While you can use a shared library to do that, it's possible to define a workflow that can be reused accross policies.
Components can be configured on instantiation, and can have some configuration done on the definition.
A simple example would be defining a component for querying an API: you can write the logic to query and treat data, configure the server parameters (endpoint, method, etc), and a user can later specify the data to be queried or the credentials to use.
