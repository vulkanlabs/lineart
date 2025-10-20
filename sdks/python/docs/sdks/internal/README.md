# Internal
(*internal*)

## Overview

### Available Operations

* [run_version_sync](#run_version_sync) - Run Version Sync
* [request_data_from_broker](#request_data_from_broker) - Request Data From Broker
* [publish_metadata](#publish_metadata) - Publish Metadata
* [update_run](#update_run) - Update Run

## run_version_sync

Execute a workflow and wait for results.

### Example Usage

<!-- UsageSnippet language="python" operationID="run_version_sync" method="post" path="/internal/run-version-sync" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.internal.run_version_sync(policy_version_id="8c0e0b71-d393-42a9-bf86-3f9f801362b3", input_data={
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

## request_data_from_broker

Request data through the data broker.

### Example Usage

<!-- UsageSnippet language="python" operationID="request_data_from_broker" method="post" path="/internal/data-broker" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.internal.request_data_from_broker(data_source_name="<value>", configured_params={

    }, run_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `data_source_name`                                                  | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `configured_params`                                                 | Dict[str, *Any*]                                                    | :heavy_check_mark:                                                  | N/A                                                                 |
| `run_id`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.DataBrokerResponse](../../models/databrokerresponse.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## publish_metadata

Publish metadata for a run step.

### Example Usage

<!-- UsageSnippet language="python" operationID="publish_metadata" method="post" path="/internal/runs/{run_id}/metadata" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.internal.publish_metadata(run_id="dbe848f3-e592-4b94-a751-dc7601bbe24b", step_name="<value>", node_type="<value>", start_time=6009.64, end_time=2185.26)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                               | Type                                                                                    | Required                                                                                | Description                                                                             |
| --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `run_id`                                                                                | *str*                                                                                   | :heavy_check_mark:                                                                      | N/A                                                                                     |
| `step_name`                                                                             | *str*                                                                                   | :heavy_check_mark:                                                                      | N/A                                                                                     |
| `node_type`                                                                             | *str*                                                                                   | :heavy_check_mark:                                                                      | N/A                                                                                     |
| `start_time`                                                                            | *float*                                                                                 | :heavy_check_mark:                                                                      | N/A                                                                                     |
| `end_time`                                                                              | *float*                                                                                 | :heavy_check_mark:                                                                      | N/A                                                                                     |
| `error`                                                                                 | [OptionalNullable[models.StepMetadataBaseError]](../../models/stepmetadatabaseerror.md) | :heavy_minus_sign:                                                                      | N/A                                                                                     |
| `extra`                                                                                 | Dict[str, *Any*]                                                                        | :heavy_minus_sign:                                                                      | N/A                                                                                     |
| `retries`                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                        | :heavy_minus_sign:                                                                      | Configuration to override the default retry behavior of the client.                     |

### Response

**[Any](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## update_run

Update run status and optionally trigger shadow runs.

### Example Usage

<!-- UsageSnippet language="python" operationID="update_run" method="put" path="/internal/runs/{run_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.internal.update_run(run_id="1eae35e9-4163-4df6-b3cf-800bde986dde", status="<value>", result="<value>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `run_id`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `status`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `result`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `metadata`                                                          | Dict[str, *Any*]                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.Run](../../models/run.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |