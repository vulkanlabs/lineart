# Runs
(*runs*)

## Overview

### Available Operations

* [get_data](#get_data) - Get Run Data
* [get_logs](#get_logs) - Get Run Logs
* [get](#get) - Get Run

## get_data

Get run data including step outputs and metadata.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_run_data" method="get" path="/runs/{run_id}/data" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.runs.get_data(run_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `run_id`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.RunData](../../models/rundata.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## get_logs

Get logs for a run.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_run_logs" method="get" path="/runs/{run_id}/logs" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.runs.get_logs(run_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `run_id`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.RunLogs](../../models/runlogs.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## get

Get run details.

### Example Usage

<!-- UsageSnippet language="python" operationID="get_run" method="get" path="/runs/{run_id}" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.runs.get(run_id="<id>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `run_id`                                                            | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.Run](../../models/run.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |