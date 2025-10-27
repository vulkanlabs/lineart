# HTTPSource


## Fields

| Field                                                             | Type                                                              | Required                                                          | Description                                                       |
| ----------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- |
| `url`                                                             | *str*                                                             | :heavy_check_mark:                                                | N/A                                                               |
| `method`                                                          | [Optional[models.Method]](../models/method.md)                    | :heavy_minus_sign:                                                | N/A                                                               |
| `headers`                                                         | Dict[str, [models.Headers6](../models/headers6.md)]               | :heavy_minus_sign:                                                | N/A                                                               |
| `params`                                                          | Dict[str, [models.Params6](../models/params6.md)]                 | :heavy_minus_sign:                                                | N/A                                                               |
| `body`                                                            | Dict[str, [models.HTTPSourceBody6](../models/httpsourcebody6.md)] | :heavy_minus_sign:                                                | N/A                                                               |
| `timeout`                                                         | *OptionalNullable[int]*                                           | :heavy_minus_sign:                                                | N/A                                                               |
| `retry`                                                           | [Optional[models.RetryPolicy]](../models/retrypolicy.md)          | :heavy_minus_sign:                                                | N/A                                                               |
| `response_type`                                                   | [Optional[models.ResponseType]](../models/responsetype.md)        | :heavy_minus_sign:                                                | N/A                                                               |