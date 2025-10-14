<!-- Start SDK Example Usage [usage] -->
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