# WorkflowBase


## Fields

| Field                                                            | Type                                                             | Required                                                         | Description                                                      |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| `spec`                                                           | [models.PolicyDefinitionDict](../models/policydefinitiondict.md) | :heavy_check_mark:                                               | Dict representation of a PolicyDefinition object.                |
| `requirements`                                                   | List[*str*]                                                      | :heavy_check_mark:                                               | N/A                                                              |
| `variables`                                                      | List[*str*]                                                      | :heavy_minus_sign:                                               | N/A                                                              |
| `ui_metadata`                                                    | Dict[str, [models.UIMetadata](../models/uimetadata.md)]          | :heavy_minus_sign:                                               | N/A                                                              |