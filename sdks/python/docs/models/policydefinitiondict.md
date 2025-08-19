# PolicyDefinitionDict

Dict representation of a PolicyDefinition object.


## Fields

| Field                                                              | Type                                                               | Required                                                           | Description                                                        |
| ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| `nodes`                                                            | List[[models.NodeDefinitionDict](../models/nodedefinitiondict.md)] | :heavy_check_mark:                                                 | N/A                                                                |
| `input_schema`                                                     | Dict[str, *str*]                                                   | :heavy_check_mark:                                                 | N/A                                                                |
| `config_variables`                                                 | List[*str*]                                                        | :heavy_minus_sign:                                                 | N/A                                                                |
| `output_callback`                                                  | *OptionalNullable[str]*                                            | :heavy_minus_sign:                                                 | N/A                                                                |