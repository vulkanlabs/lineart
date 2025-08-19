# DataSourceSpec


## Fields

| Field                                                            | Type                                                             | Required                                                         | Description                                                      |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| `name`                                                           | *str*                                                            | :heavy_check_mark:                                               | N/A                                                              |
| `source`                                                         | [models.DataSourceSpecSource](../models/datasourcespecsource.md) | :heavy_check_mark:                                               | N/A                                                              |
| `caching`                                                        | [Optional[models.CachingOptions]](../models/cachingoptions.md)   | :heavy_minus_sign:                                               | N/A                                                              |
| `description`                                                    | *OptionalNullable[str]*                                          | :heavy_minus_sign:                                               | N/A                                                              |
| `metadata`                                                       | Dict[str, *Any*]                                                 | :heavy_minus_sign:                                               | N/A                                                              |