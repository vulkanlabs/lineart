# NodeDefinitionDict

Dict representation of a NodeDefinition object.


## Fields

| Field                                                           | Type                                                            | Required                                                        | Description                                                     |
| --------------------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------- |
| `name`                                                          | *str*                                                           | :heavy_check_mark:                                              | N/A                                                             |
| `node_type`                                                     | *str*                                                           | :heavy_check_mark:                                              | N/A                                                             |
| `dependencies`                                                  | Dict[str, [models.DependencyDict](../models/dependencydict.md)] | :heavy_minus_sign:                                              | N/A                                                             |
| `metadata`                                                      | Dict[str, *Any*]                                                | :heavy_minus_sign:                                              | N/A                                                             |
| `description`                                                   | *OptionalNullable[str]*                                         | :heavy_minus_sign:                                              | N/A                                                             |
| `hierarchy`                                                     | List[*str*]                                                     | :heavy_minus_sign:                                              | N/A                                                             |