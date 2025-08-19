# HTTPSource


## Fields

| Field                                                      | Type                                                       | Required                                                   | Description                                                |
| ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- |
| `url`                                                      | *str*                                                      | :heavy_check_mark:                                         | N/A                                                        |
| `method`                                                   | [Optional[models.Method]](../models/method.md)             | :heavy_minus_sign:                                         | N/A                                                        |
| `headers`                                                  | Dict[str, [models.Headers2](../models/headers2.md)]        | :heavy_minus_sign:                                         | N/A                                                        |
| `params`                                                   | Dict[str, [models.Params2](../models/params2.md)]          | :heavy_minus_sign:                                         | N/A                                                        |
| `body`                                                     | Dict[str, [models.Body2](../models/body2.md)]              | :heavy_minus_sign:                                         | N/A                                                        |
| `timeout`                                                  | *OptionalNullable[int]*                                    | :heavy_minus_sign:                                         | N/A                                                        |
| `retry`                                                    | [Optional[models.RetryPolicy]](../models/retrypolicy.md)   | :heavy_minus_sign:                                         | N/A                                                        |
| `response_type`                                            | [Optional[models.ResponseType]](../models/responsetype.md) | :heavy_minus_sign:                                         | N/A                                                        |