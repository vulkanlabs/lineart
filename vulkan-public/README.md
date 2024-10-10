# Vulkan

## Overview

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

We provide a couple of simple examples in `sample-user-policies/examples/components`.

## Installation

### [Vulkan](https://github.com/vulkanlabs/vulkan-public) Lib & CLI

The main entrypoint for Vulkan functionality.

Currently, you need to install this package from source.
After that, the CLI and Python client library can be used to manage your policies.

```bash
git clone https://github.com/vulkanlabs/vulkan-public.git
cd vulkan-public
pip install .

# Test the CLI & Authenticate
vulkan --help
```

### [Examples](https://github.com/vulkanlabs/sample-user-policy)

We've added a couple of examples in a separate repo.
```bash
git clone https://github.com/vulkanlabs/sample-user-policy.git
```

## CLI Usage

### Authenticating

The CLI uses the same credentials used as the website.
To login, and later to refresh credentials run:
```bash
vulkan login
```

If your credentials are valid - or if the session can be refreshed - you won't be prompted for access.

### Creating a Policy

The script below creates a sample policy:
```bash
vulkan policy create --name my-policy

# INFO Created policy my-policy with id <POLICY_ID>

vulkan policy create-version \
    --policy_id <POLICY_ID> \
    --version_name "my-first-policy-version" \
    --repository_path sample-user-policy/examples/policies/base

# INFO Created workspace my-first-policy-version with policy version <POLICY_VERSION_ID>

vulkan policy set-active-version \
    --policy_id <POLICY_ID> \
    --policy_version_id <POLICY_VERSION_ID>
```

### Triggering a Policy Run

Its possible to trigger a run for a Policy or for any specific Policy Version.
In both cases, you only need to pass the ID and the required data. Data should be passed as a JSON string.
```bash
# By Policy ID
vulkan policy trigger-run \
    --policy_id <POLICY_ID> \
    --data '{"key1": "value1", "key2": 2}'

# By Policy Version ID
vulkan policy trigger-run-by-version \
    --policy_version_id <POLICY_VERSION_ID> \
    --data '{"key1": "value1", "key2": 2}'
```

### Retrieving data from a Run

To retrieve the data from a single run:
```bash
vulkan run data <RUN_ID>
```

We don't have a method to extract data in bulk yet.
You can sort of improvise that by iterating over individual runs.

