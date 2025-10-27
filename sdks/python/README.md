# lineart-sdk

Developer-friendly & type-safe Python SDK specifically catered to leverage *lineart-sdk* API.

<div align="left">
    <a href="https://www.speakeasy.com/?utm_source=lineart-sdk&utm_campaign=python"><img src="https://custom-icon-badges.demolab.com/badge/-Built%20By%20Speakeasy-212015?style=for-the-badge&logoColor=FBE331&logo=speakeasy&labelColor=545454" /></a>
    <a href="https://opensource.org/licenses/MIT">
        <img src="https://img.shields.io/badge/License-MIT-blue.svg" style="width: 100px; height: 28px;" />
    </a>
</div>


<br /><br />
> [!IMPORTANT]
> This SDK is not yet ready for production use. To complete setup please follow the steps outlined in your [workspace](https://app.speakeasy.com/org/vulkan/lineart). Delete this section before > publishing to a package manager.

<!-- Start Summary [summary] -->
## Summary


<!-- End Summary [summary] -->

<!-- Start Table of Contents [toc] -->
## Table of Contents
<!-- $toc-max-depth=2 -->
* [lineart-sdk](#lineart-sdk)
  * [SDK Installation](#sdk-installation)
  * [IDE Support](#ide-support)
  * [SDK Example Usage](#sdk-example-usage)
  * [Available Resources and Operations](#available-resources-and-operations)
  * [Retries](#retries)
  * [Error Handling](#error-handling)
  * [Custom HTTP Client](#custom-http-client)
  * [Resource Management](#resource-management)
  * [Debugging](#debugging)
* [Development](#development)
  * [Maturity](#maturity)
  * [Contributions](#contributions)

<!-- End Table of Contents [toc] -->

<!-- Start SDK Installation [installation] -->
## SDK Installation

> [!TIP]
> To finish publishing your SDK to PyPI you must [run your first generation action](https://www.speakeasy.com/docs/github-setup#step-by-step-guide).


> [!NOTE]
> **Python version upgrade policy**
>
> Once a Python version reaches its [official end of life date](https://devguide.python.org/versions/), a 3-month grace period is provided for users to upgrade. Following this grace period, the minimum python version supported in the SDK will be updated.

The SDK can be installed with *uv*, *pip*, or *poetry* package managers.

### uv

*uv* is a fast Python package installer and resolver, designed as a drop-in replacement for pip and pip-tools. It's recommended for its speed and modern Python tooling capabilities.

```bash
uv add git+<UNSET>.git
```

### PIP

*PIP* is the default package installer for Python, enabling easy installation and management of packages from PyPI via the command line.

```bash
pip install git+<UNSET>.git
```

### Poetry

*Poetry* is a modern tool that simplifies dependency management and package publishing by using a single `pyproject.toml` file to handle project metadata and dependencies.

```bash
poetry add git+<UNSET>.git
```

### Shell and script usage with `uv`

You can use this SDK in a Python shell with [uv](https://docs.astral.sh/uv/) and the `uvx` command that comes with it like so:

```shell
uvx --from lineart-sdk python
```

It's also possible to write a standalone Python script without needing to set up a whole project like so:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "lineart-sdk",
# ]
# ///

from lineart_sdk import Lineart

sdk = Lineart(
  # SDK arguments
)

# Rest of script here...
```

Once that is saved to a file, you can run it with `uv run script.py` where
`script.py` can be replaced with the actual file name.
<!-- End SDK Installation [installation] -->

<!-- Start IDE Support [idesupport] -->
## IDE Support

### PyCharm

Generally, the SDK will work well with most IDEs out of the box. However, when using PyCharm, you can enjoy much better integration with Pydantic by installing an additional plugin.

- [PyCharm Pydantic Plugin](https://docs.pydantic.dev/latest/integrations/pycharm/)
<!-- End IDE Support [idesupport] -->

<!-- Start SDK Example Usage [usage] -->
## SDK Example Usage

### Example

```python
# Synchronous Example
from lineart_sdk import Lineart


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.components.list(include_archived=False)

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from lineart_sdk import Lineart

async def main():

    async with Lineart(
        server_url="https://api.example.com",
    ) as lineart:

        res = await lineart.components.list_async(include_archived=False)

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->

<!-- Start Available Resources and Operations [operations] -->
## Available Resources and Operations

<details open>
<summary>Available methods</summary>

### [auth](docs/sdks/auth/README.md)

* [start](docs/sdks/auth/README.md#start) - Start Auth
* [get_user_info](docs/sdks/auth/README.md#get_user_info) - Get User Info
* [disconnect](docs/sdks/auth/README.md#disconnect) - Disconnect
* [callback](docs/sdks/auth/README.md#callback) - Auth Callback

### [components](docs/sdks/components/README.md)

* [list](docs/sdks/components/README.md#list) - List Components
* [create](docs/sdks/components/README.md#create) - Create Component
* [get_component](docs/sdks/components/README.md#get_component) - Get Component
* [update_component](docs/sdks/components/README.md#update_component) - Update Component
* [delete_component](docs/sdks/components/README.md#delete_component) - Delete Component

### [data_sources](docs/sdks/datasources/README.md)

* [list](docs/sdks/datasources/README.md#list) - List Data Sources
* [create](docs/sdks/datasources/README.md#create) - Create Data Source
* [get](docs/sdks/datasources/README.md#get) - Get Data Source
* [delete](docs/sdks/datasources/README.md#delete) - Delete Data Source
* [set_env_variables](docs/sdks/datasources/README.md#set_env_variables) - Set Data Source Env Variables
* [get_object](docs/sdks/datasources/README.md#get_object) - Get Data Object
* [get_metrics](docs/sdks/datasources/README.md#get_metrics) - Get Data Source Metrics
* [get_cache_statistics](docs/sdks/datasources/README.md#get_cache_statistics) - Get Cache Statistics
* [update_data_source](docs/sdks/datasources/README.md#update_data_source) - Update Data Source
* [get_env_variables](docs/sdks/datasources/README.md#get_env_variables) - Get Data Source Env Variables
* [list_data_objects](docs/sdks/datasources/README.md#list_data_objects) - List Data Objects
* [get_usage](docs/sdks/datasources/README.md#get_usage) - Get Data Source Usage
* [publish_data_source](docs/sdks/datasources/README.md#publish_data_source) - Publish Data Source
* [test_data_source](docs/sdks/datasources/README.md#test_data_source) - Test Data Source
* [test_data_source_by_id](docs/sdks/datasources/README.md#test_data_source_by_id) - Test Data Source By Id

### [internal](docs/sdks/internal/README.md)

* [run_version_sync](docs/sdks/internal/README.md#run_version_sync) - Run Version Sync
* [request_data_from_broker](docs/sdks/internal/README.md#request_data_from_broker) - Request Data From Broker
* [publish_metadata](docs/sdks/internal/README.md#publish_metadata) - Publish Metadata
* [update_run](docs/sdks/internal/README.md#update_run) - Update Run

### [policies](docs/sdks/policies/README.md)

* [list](docs/sdks/policies/README.md#list) - List Policies
* [create](docs/sdks/policies/README.md#create) - Create Policy
* [get](docs/sdks/policies/README.md#get) - Get Policy
* [update](docs/sdks/policies/README.md#update) - Update Policy
* [delete](docs/sdks/policies/README.md#delete) - Delete Policy
* [list_versions](docs/sdks/policies/README.md#list_versions) - List Policy Versions By Policy
* [list_runs](docs/sdks/policies/README.md#list_runs) - List Runs By Policy
* [create_run_group](docs/sdks/policies/README.md#create_run_group) - Create Run Group
* [run_duration_stats_by_policy](docs/sdks/policies/README.md#run_duration_stats_by_policy) - Run Duration Stats By Policy
* [run_duration_stats_by_policy_status](docs/sdks/policies/README.md#run_duration_stats_by_policy_status) - Run Duration Stats By Policy Status
* [runs_by_policy](docs/sdks/policies/README.md#runs_by_policy) - Runs By Policy
* [runs_outcomes_by_policy](docs/sdks/policies/README.md#runs_outcomes_by_policy) - Runs Outcomes By Policy

### [policy_versions](docs/sdks/policyversions/README.md)

* [create](docs/sdks/policyversions/README.md#create) - Create Policy Version
* [update](docs/sdks/policyversions/README.md#update) - Update Policy Version
* [delete](docs/sdks/policyversions/README.md#delete) - Delete Policy Version
* [create_run](docs/sdks/policyversions/README.md#create_run) - Create Run By Policy Version
* [list_config_variables](docs/sdks/policyversions/README.md#list_config_variables) - List Config Variables
* [set_config_variables](docs/sdks/policyversions/README.md#set_config_variables) - Set Config Variables
* [list_data_sources](docs/sdks/policyversions/README.md#list_data_sources) - List Data Sources By Policy Version
* [list](docs/sdks/policyversions/README.md#list) - List Policy Versions
* [get](docs/sdks/policyversions/README.md#get) - Get Policy Version
* [list_runs](docs/sdks/policyversions/README.md#list_runs) - List Runs By Policy Version
* [run_workflow](docs/sdks/policyversions/README.md#run_workflow) - Run Workflow

### [runs](docs/sdks/runs/README.md)

* [get_data](docs/sdks/runs/README.md#get_data) - Get Run Data
* [get_logs](docs/sdks/runs/README.md#get_logs) - Get Run Logs
* [get](docs/sdks/runs/README.md#get) - Get Run

</details>
<!-- End Available Resources and Operations [operations] -->

<!-- Start Retries [retries] -->
## Retries

Some of the endpoints in this SDK support retries. If you use the SDK without any configuration, it will fall back to the default retry strategy provided by the API. However, the default retry strategy can be overridden on a per-operation basis, or across the entire SDK.

To change the default retry strategy for a single API call, simply provide a `RetryConfig` object to the call:
```python
from lineart_sdk import Lineart
from lineart_sdk.utils import BackoffStrategy, RetryConfig


with Lineart(
    server_url="https://api.example.com",
) as lineart:

    res = lineart.components.list(include_archived=False,
        RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False))

    # Handle response
    print(res)

```

If you'd like to override the default retry strategy for all operations that support retries, you can use the `retry_config` optional parameter when initializing the SDK:
```python
from lineart_sdk import Lineart
from lineart_sdk.utils import BackoffStrategy, RetryConfig


with Lineart(
    server_url="https://api.example.com",
    retry_config=RetryConfig("backoff", BackoffStrategy(1, 50, 1.1, 100), False),
) as lineart:

    res = lineart.components.list(include_archived=False)

    # Handle response
    print(res)

```
<!-- End Retries [retries] -->

<!-- Start Error Handling [errors] -->
## Error Handling

[`LineartError`](./src/lineart_sdk/errors/linearterror.py) is the base class for all HTTP error responses. It has the following properties:

| Property           | Type             | Description                                                                             |
| ------------------ | ---------------- | --------------------------------------------------------------------------------------- |
| `err.message`      | `str`            | Error message                                                                           |
| `err.status_code`  | `int`            | HTTP response status code eg `404`                                                      |
| `err.headers`      | `httpx.Headers`  | HTTP response headers                                                                   |
| `err.body`         | `str`            | HTTP body. Can be empty string if no body is returned.                                  |
| `err.raw_response` | `httpx.Response` | Raw HTTP response                                                                       |
| `err.data`         |                  | Optional. Some errors may contain structured data. [See Error Classes](#error-classes). |

### Example
```python
from lineart_sdk import Lineart, errors


with Lineart(
    server_url="https://api.example.com",
) as lineart:
    res = None
    try:

        res = lineart.components.list(include_archived=False)

        # Handle response
        print(res)


    except errors.LineartError as e:
        # The base class for HTTP error responses
        print(e.message)
        print(e.status_code)
        print(e.body)
        print(e.headers)
        print(e.raw_response)

        # Depending on the method different errors may be thrown
        if isinstance(e, errors.HTTPValidationError):
            print(e.data.detail)  # Optional[List[models.ValidationError]]
```

### Error Classes
**Primary errors:**
* [`LineartError`](./src/lineart_sdk/errors/linearterror.py): The base class for HTTP error responses.
  * [`HTTPValidationError`](./src/lineart_sdk/errors/httpvalidationerror.py): Validation Error. Status code `422`.

<details><summary>Less common errors (5)</summary>

<br />

**Network errors:**
* [`httpx.RequestError`](https://www.python-httpx.org/exceptions/#httpx.RequestError): Base class for request errors.
    * [`httpx.ConnectError`](https://www.python-httpx.org/exceptions/#httpx.ConnectError): HTTP client was unable to make a request to a server.
    * [`httpx.TimeoutException`](https://www.python-httpx.org/exceptions/#httpx.TimeoutException): HTTP request timed out.


**Inherit from [`LineartError`](./src/lineart_sdk/errors/linearterror.py)**:
* [`ResponseValidationError`](./src/lineart_sdk/errors/responsevalidationerror.py): Type mismatch between the response data and the expected Pydantic model. Provides access to the Pydantic validation error via the `cause` attribute.

</details>
<!-- End Error Handling [errors] -->

<!-- Start Custom HTTP Client [http-client] -->
## Custom HTTP Client

The Python SDK makes API calls using the [httpx](https://www.python-httpx.org/) HTTP library.  In order to provide a convenient way to configure timeouts, cookies, proxies, custom headers, and other low-level configuration, you can initialize the SDK client with your own HTTP client instance.
Depending on whether you are using the sync or async version of the SDK, you can pass an instance of `HttpClient` or `AsyncHttpClient` respectively, which are Protocol's ensuring that the client has the necessary methods to make API calls.
This allows you to wrap the client with your own custom logic, such as adding custom headers, logging, or error handling, or you can just pass an instance of `httpx.Client` or `httpx.AsyncClient` directly.

For example, you could specify a header for every request that this sdk makes as follows:
```python
from lineart_sdk import Lineart
import httpx

http_client = httpx.Client(headers={"x-custom-header": "someValue"})
s = Lineart(client=http_client)
```

or you could wrap the client with your own custom logic:
```python
from lineart_sdk import Lineart
from lineart_sdk.httpclient import AsyncHttpClient
import httpx

class CustomClient(AsyncHttpClient):
    client: AsyncHttpClient

    def __init__(self, client: AsyncHttpClient):
        self.client = client

    async def send(
        self,
        request: httpx.Request,
        *,
        stream: bool = False,
        auth: Union[
            httpx._types.AuthTypes, httpx._client.UseClientDefault, None
        ] = httpx.USE_CLIENT_DEFAULT,
        follow_redirects: Union[
            bool, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
    ) -> httpx.Response:
        request.headers["Client-Level-Header"] = "added by client"

        return await self.client.send(
            request, stream=stream, auth=auth, follow_redirects=follow_redirects
        )

    def build_request(
        self,
        method: str,
        url: httpx._types.URLTypes,
        *,
        content: Optional[httpx._types.RequestContent] = None,
        data: Optional[httpx._types.RequestData] = None,
        files: Optional[httpx._types.RequestFiles] = None,
        json: Optional[Any] = None,
        params: Optional[httpx._types.QueryParamTypes] = None,
        headers: Optional[httpx._types.HeaderTypes] = None,
        cookies: Optional[httpx._types.CookieTypes] = None,
        timeout: Union[
            httpx._types.TimeoutTypes, httpx._client.UseClientDefault
        ] = httpx.USE_CLIENT_DEFAULT,
        extensions: Optional[httpx._types.RequestExtensions] = None,
    ) -> httpx.Request:
        return self.client.build_request(
            method,
            url,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            extensions=extensions,
        )

s = Lineart(async_client=CustomClient(httpx.AsyncClient()))
```
<!-- End Custom HTTP Client [http-client] -->

<!-- Start Resource Management [resource-management] -->
## Resource Management

The `Lineart` class implements the context manager protocol and registers a finalizer function to close the underlying sync and async HTTPX clients it uses under the hood. This will close HTTP connections, release memory and free up other resources held by the SDK. In short-lived Python programs and notebooks that make a few SDK method calls, resource management may not be a concern. However, in longer-lived programs, it is beneficial to create a single SDK instance via a [context manager][context-manager] and reuse it across the application.

[context-manager]: https://docs.python.org/3/reference/datamodel.html#context-managers

```python
from lineart_sdk import Lineart
def main():

    with Lineart(
        server_url="https://api.example.com",
    ) as lineart:
        # Rest of application here...


# Or when using async:
async def amain():

    async with Lineart(
        server_url="https://api.example.com",
    ) as lineart:
        # Rest of application here...
```
<!-- End Resource Management [resource-management] -->

<!-- Start Debugging [debug] -->
## Debugging

You can setup your SDK to emit debug logs for SDK requests and responses.

You can pass your own logger class directly into your SDK.
```python
from lineart_sdk import Lineart
import logging

logging.basicConfig(level=logging.DEBUG)
s = Lineart(server_url="https://example.com", debug_logger=logging.getLogger("lineart_sdk"))
```

You can also enable a default debug logger by setting an environment variable `LINEART_DEBUG` to true.
<!-- End Debugging [debug] -->

<!-- Placeholder for Future Speakeasy SDK Sections -->

# Development

## Maturity

This SDK is in beta, and there may be breaking changes between versions without a major version update. Therefore, we recommend pinning usage
to a specific package version. This way, you can install the same version each time without breaking changes unless you are intentionally
looking for the latest version.

## Contributions

While we value open-source contributions to this SDK, this library is generated programmatically. Any manual changes added to internal files will be overwritten on the next generation. 
We look forward to hearing your feedback. Feel free to open a PR or an issue with a proof of concept and we'll do our best to include it in a future release. 

### SDK Created by [Speakeasy](https://www.speakeasy.com/?utm_source=lineart-sdk&utm_campaign=python)
