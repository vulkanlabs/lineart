# Auth
(*auth*)

## Overview

### Available Operations

* [start](#start) - Start Auth
* [get_user_info](#get_user_info) - Get User Info
* [disconnect](#disconnect) - Disconnect
* [callback](#callback) - Auth Callback

## start

Initiates the OAuth2 flow for a given service.

### Example Usage

<!-- UsageSnippet language="python" operationID="start_auth" method="get" path="/auth/{service_name}/start" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.auth.start(service_name="<value>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `service_name`                                                      | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `project_id`                                                        | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.AuthStartResponse](../../models/authstartresponse.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## get_user_info

Get User Info

### Example Usage

<!-- UsageSnippet language="python" operationID="get_user_info" method="get" path="/auth/{service_name}/user_info" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.auth.get_user_info(service_name="<value>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `service_name`                                                      | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `project_id`                                                        | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.AuthUserInfoResponse](../../models/authuserinforesponse.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## disconnect

Disconnect

### Example Usage

<!-- UsageSnippet language="python" operationID="disconnect" method="post" path="/auth/{service_name}/disconnect" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.auth.disconnect(service_name="<value>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `service_name`                                                      | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `project_id`                                                        | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.AuthDisconnectResponse](../../models/authdisconnectresponse.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |

## callback

Handles the callback from the OAuth provider.

### Example Usage

<!-- UsageSnippet language="python" operationID="auth_callback" method="get" path="/auth/{service_name}/callback" -->
```python
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.auth.callback(service_name="<value>")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `service_name`                                                      | *str*                                                               | :heavy_check_mark:                                                  | N/A                                                                 |
| `code`                                                              | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `state`                                                             | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `error`                                                             | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `project_id`                                                        | *OptionalNullable[str]*                                             | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[Any](../../models/.md)**

### Errors

| Error Type                 | Status Code                | Content Type               |
| -------------------------- | -------------------------- | -------------------------- |
| errors.HTTPValidationError | 422                        | application/json           |
| errors.LineartDefaultError | 4XX, 5XX                   | \*/\*                      |