# Policies
(*policies*)

## Overview

### Available Operations

* [list](#list) - List Policies
* [create](#create) - Create Policy
* [get](#get) - Get Policy
* [update](#update) - Update Policy
* [delete](#delete) - Delete Policy
* [list_versions](#list_versions) - List Policy Versions By Policy
* [list_runs](#list_runs) - List Runs By Policy
* [create_run_group](#create_run_group) - Create Run Group
* [run_duration_stats_by_policy](#run_duration_stats_by_policy) - Run Duration Stats By Policy
* [run_duration_stats_by_policy_status](#run_duration_stats_by_policy_status) - Run Duration Stats By Policy Status
* [runs_by_policy](#runs_by_policy) - Runs By Policy
* [runs_outcomes_by_policy](#runs_outcomes_by_policy) - Runs Outcomes By Policy

## list

List all policies.

### Example Usage

<!-- UsageSnippet language="python" operationID="list_policies" method="get" path="/policies/" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.list(include_archived=False)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `include_archived`                                                  | *Optional[bool]*                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[List[models.Policy]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## create

Create a new policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="create_policy" method="post" path="/policies/" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.create(name="<value>", description="")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `name`                                                              | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `description`                                                       | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.Policy](../../models/policy.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## get

Get a policy by ID.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_policy" method="get" path="/policies/{policy_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.get(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_id`                                                         | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.Policy](../../models/policy.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## update

Update a policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="update_policy" method="put" path="/policies/{policy_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.update(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                     | Type                                                                                          | Required                                                                                      | Description                                                                                   |
| --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `policy_id`                                                                                   | *str*                                                                                         | :heavy_check_mark:                                                                            | N/A                                                                                           |
| `name`                                                                                        | *OptionalNullable[str]*                                                                       | :heavy_minus_sign:                                                                            | N/A                                                                                           |
| `description`                                                                                 | *OptionalNullable[str]*                                                                       | :heavy_minus_sign:                                                                            | N/A                                                                                           |
| `allocation_strategy`                                                                         | [OptionalNullable[models.PolicyAllocationStrategy]](../../models/policyallocationstrategy.md) | :heavy_minus_sign:                                                                            | N/A                                                                                           |
| `retries`                                                                                     | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                              | :heavy_minus_sign:                                                                            | Configuration to override the default retry behavior of the client.                           |

### Response

**[models.Policy](../../models/policy.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## delete

Delete (archive) a policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="delete_policy" method="delete" path="/policies/{policy_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.delete(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_id`                                                         | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[Any](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## list_versions

List versions for a policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="list_policy_versions_by_policy" method="get" path="/policies/{policy_id}/versions" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.list_versions(policy_id="<id>", include_archived=False)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `policy_id`                                                         | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `include_archived`                                                  | *Optional[bool]*                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[List[models.PolicyVersion]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## list_runs

List runs for a policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="list_runs_by_policy" method="get" path="/policies/{policy_id}/runs" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.list_runs(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                            | Type                                                                 | Required                                                             | Description                                                          |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `policy_id`                                                          | *str*                                                                | :heavy_check_mark:                                                   | N/A                                                                  |
| `start_date`                                                         | [date](https://docs.python.org/3/library/datetime.html#date-objects) | :heavy_minus_sign:                                                   | N/A                                                                  |
| `end_date`                                                           | [date](https://docs.python.org/3/library/datetime.html#date-objects) | :heavy_minus_sign:                                                   | N/A                                                                  |
| `retries`                                                            | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)     | :heavy_minus_sign:                                                   | Configuration to override the default retry behavior of the client.  |

### Response

**[List[models.Run]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## create_run_group

Create a run group and allocate runs.

### Example Usage

<!-- UsageSnippet language="python" operationID="create_run_group" method="post" path="/policies/{policy_id}/runs" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.create_run_group(policy_id="<id>", input_data={
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
| `policy_id`                                                         | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `input_data`                                                        | Dict[str, *Any*]                                                    | :heavy_check_mark:                                                  | N/A                                                                 |
| `config_variables`                                                  | Dict[str, *Any*]                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.RunGroupResult](../../models/rungroupresult.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## run_duration_stats_by_policy

Get run duration statistics for a policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="run_duration_stats_by_policy" method="post" path="/policies/{policy_id}/runs/duration/query" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.run_duration_stats_by_policy(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `policy_id`                                                                  | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          |
| `start_date`                                                                 | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `end_date`                                                                   | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `versions`                                                                   | List[*str*]                                                                  | :heavy_minus_sign:                                                           | N/A                                                                          |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |

### Response

**[List[Any]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## run_duration_stats_by_policy_status

Get run duration statistics grouped by status.

### Example Usage

<!-- UsageSnippet language="python" operationID="run_duration_stats_by_policy_status" method="post" path="/policies/{policy_id}/runs/duration/by_status/query" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.run_duration_stats_by_policy_status(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `policy_id`                                                                  | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          |
| `start_date`                                                                 | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `end_date`                                                                   | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `versions`                                                                   | List[*str*]                                                                  | :heavy_minus_sign:                                                           | N/A                                                                          |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |

### Response

**[List[Any]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## runs_by_policy

Get run counts and error rates for a policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="runs_by_policy" method="post" path="/policies/{policy_id}/runs/count/query" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.runs_by_policy(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `policy_id`                                                                  | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          |
| `start_date`                                                                 | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `end_date`                                                                   | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `versions`                                                                   | List[*str*]                                                                  | :heavy_minus_sign:                                                           | N/A                                                                          |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |

### Response

**[List[Any]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## runs_outcomes_by_policy

Get run outcome distribution for a policy.

### Example Usage

<!-- UsageSnippet language="python" operationID="runs_outcomes_by_policy" method="post" path="/policies/{policy_id}/runs/outcomes/query" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.policies.runs_outcomes_by_policy(policy_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                    | Type                                                                         | Required                                                                     | Description                                                                  |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `policy_id`                                                                  | *str*                                                                        | :heavy_check_mark:                                                           | N/A                                                                          |
| `start_date`                                                                 | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `end_date`                                                                   | [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects) | :heavy_minus_sign:                                                           | N/A                                                                          |
| `versions`                                                                   | List[*str*]                                                                  | :heavy_minus_sign:                                                           | N/A                                                                          |
| `retries`                                                                    | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)             | :heavy_minus_sign:                                                           | Configuration to override the default retry behavior of the client.          |

### Response

**[List[Any]](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |