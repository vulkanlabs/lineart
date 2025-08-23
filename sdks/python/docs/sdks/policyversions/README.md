# PolicyVersions
(*policy_versions*)

## Overview

### Available Operations

* [create](#create) - Create Policy Version
* [update](#update) - Update Policy Version
* [delete](#delete) - Delete Policy Version
* [create_run](#create_run) - Create Run By Policy Version
* [list_config_variables](#list_config_variables) - List Config Variables
* [set_config_variables](#set_config_variables) - Set Config Variables
* [list_data_sources](#list_data_sources) - List Data Sources By Policy Version
* [list](#list) - List Policy Versions
* [get](#get) - Get Policy Version
* [list_runs](#list_runs) - List Runs By Policy Version
* [run_workflow](#run_workflow) - Run Workflow

## create

Create a new policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="create_policy_version" method="post" path="/policy-versions/" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.create(policy_id="d5d23c1a-3798-494a-8b08-d6f3a58f856b", alias="<value>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_id`                                                         | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `alias`                                                             | *Nullable[str]*                                                     | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PolicyVersion](../../models/policyversion.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## update

Update a policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="update_policy_version" method="put" path="/policy-versions/{policy_version_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.update(policy_version_id="<id>", alias="<value>", workflow={
        "spec": {
            "nodes": [],
            "input_schema": {
                "key": "<value>",
                "key1": "<value>",
            },
        },
        "requirements": [
            "<value 1>",
            "<value 2>",
            "<value 3>",
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_version_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `alias`                                                             | *Nullable[str]*                                                     | :heavy_check_mark:                                                  | N/A                                                                 |
| `workflow`                                                          | [models.WorkflowBase](../../models/workflowbase.md)                 | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PolicyVersion](../../models/policyversion.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## delete

Delete (archive) a policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_policy_version" method="delete" path="/policy-versions/{policy_version_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.delete(policy_version_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_version_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[Any](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## create_run

Create a run for a policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="create_run_by_policy_version" method="post" path="/policy-versions/{policy_version_id}/runs" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.create_run(policy_version_id="<id>", input_data={
        "key": "<value>",
        "key1": "<value>",
        "key2": "<value>",
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_version_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `input_data`                                                        | Dict[str, *Any*]                                                    | :heavy_check_mark:                                                  | N/A                                                                 |
| `config_variables`                                                  | Dict[str, *Any*]                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.RunCreated](../../models/runcreated.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## list_config_variables

List configuration variables for a policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="list_config_variables" method="get" path="/policy-versions/{policy_version_id}/variables" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.list_config_variables(policy_version_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_version_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[List[models.ConfigurationVariables]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## set_config_variables

Set configuration variables for a policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="set_config_variables" method="put" path="/policy-versions/{policy_version_id}/variables" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.set_config_variables(policy_version_id="<id>", request_body=[
        {
            "name": "<value>",
        },
    ])

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                             | Type                                                                                  | Required                                                                              | Description                                                                           |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `policy_version_id`                                                                   | *str*                                                                                 | :heavy_check_mark:                                                                    | N/A                                                                                   |
| `request_body`                                                                        | List[[models.ConfigurationVariablesBase](../../models/configurationvariablesbase.md)] | :heavy_check_mark:                                                                    | N/A                                                                                   |
| `retries`                                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                      | :heavy_minus_sign:                                                                    | Configuration to override the default retry behavior of the client.                   |

### Response

**[Any](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## list_data_sources

List data sources used by a policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="list_data_sources_by_policy_version" method="get" path="/policy-versions/{policy_version_id}/data-sources" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.list_data_sources(policy_version_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_version_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[List[models.DataSourceReference]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## list

List policy versions with optional filtering.

### Example Usage

<!-- UsageSnippet language="python" operationID="list_policy_versions" method="get" path="/policy-versions/" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.list(include_archived=False)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_id`                                                         | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `include_archived`                                                  | *Optional[bool]*                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[List[models.PolicyVersion]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## get

Get a policy version by ID.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_policy_version" method="get" path="/policy-versions/{policy_version_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.get(policy_version_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_version_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.PolicyVersion](../../models/policyversion.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## list_runs

List runs for a policy version.

### Example Usage

<!-- UsageSnippet language="python" operationID="list_runs_by_policy_version" method="get" path="/policy-versions/{policy_version_id}/runs" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.list_runs(policy_version_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `policy_version_id`                                                          | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          |
| `start_date`                                                                 | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `end_date`                                                                   | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |

### Response

**[List[models.Run]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## run_workflow

Execute a workflow and wait for results.

### Example Usage

<!-- UsageSnippet language="python" operationID="run_workflow" method="post" path="/policy-versions/{policy_version_id}/run" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policy_versions.run_workflow(policy_version_id="<id>", input_data={
        "key": "<value>",
        "key1": "<value>",
        "key2": "<value>",
    }, polling_interval_ms=500, polling_timeout_ms=300000)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_version_id`                                                 | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `input_data`                                                        | Dict[str, *Any*]                                                    | :heavy_check_mark:                                                  | N/A                                                                 |
| `polling_interval_ms`                                               | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |
| `polling_timeout_ms`                                                | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |
| `config_variables`                                                  | Dict[str, *Any*]                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.RunResult](../../models/runresult.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |