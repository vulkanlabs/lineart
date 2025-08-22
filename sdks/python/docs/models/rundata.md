# RunData


## Fields

| Field                                                                | Type                                                                 | Required                                                             | Description                                                          |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `run_id`                                                             | *str*                                                                | :heavy_check_mark:                                                   | N/A                                                                  |
| `policy_version_id`                                                  | *str*                                                                | :heavy_check_mark:                                                   | N/A                                                                  |
| `status`                                                             | *str*                                                                | :heavy_check_mark:                                                   | N/A                                                                  |
| `last_updated_at`                                                    | [date](https://docs.python.org/3/library/datetime.html#date-objects) | :heavy_check_mark:                                                   | N/A                                                                  |
| `steps`                                                              | Dict[str, [models.StepDetails](../models/stepdetails.md)]            | :heavy_check_mark:                                                   | N/A                                                                  |