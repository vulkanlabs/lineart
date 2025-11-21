# AuthConfig

Unified authentication configuration for DataSources.

The auth config defines HOW to authenticate (method, endpoints, etc).
The actual credentials (CLIENT_ID, CLIENT_SECRET) are configured separately
via environment variables and stored securely in the database.

Configuration Flow:
    1. User creates DataSource with AuthConfig (this object)
    2. User separately sets CLIENT_ID and CLIENT_SECRET as env vars
    3. Backend stores credentials securely (CLIENT_SECRET encrypted)
    4. At runtime, credentials are retrieved and used with this auth config


## Fields

| Field                                                        | Type                                                         | Required                                                     | Description                                                  | Example                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `method`                                                     | [models.AuthMethod](../models/authmethod.md)                 | :heavy_check_mark:                                           | N/A                                                          |                                                              |
| `token_url`                                                  | *OptionalNullable[str]*                                      | :heavy_minus_sign:                                           | OAuth token endpoint URL (required for bearer auth)          | https://api.example.com/oauth/token                          |
| `grant_type`                                                 | [OptionalNullable[models.GrantType]](../models/granttype.md) | :heavy_minus_sign:                                           | OAuth grant type (required for bearer auth)                  |                                                              |
| `scope`                                                      | *OptionalNullable[str]*                                      | :heavy_minus_sign:                                           | OAuth scope - space-separated list (optional)                | api.read api.write                                           |