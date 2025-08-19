# RunLogs


## Fields

| Field                                                                | Type                                                                 | Required                                                             | Description                                                          |
| -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `run_id`                                                             | *str*                                                                | :heavy_check_mark:                                                   | N/A                                                                  |
| `status`                                                             | *str*                                                                | :heavy_check_mark:                                                   | N/A                                                                  |
| `last_updated_at`                                                    | [date](https://docs.python.org/3/library/datetime.html#date-objects) | :heavy_check_mark:                                                   | N/A                                                                  |
| `logs`                                                               | List[[models.LogEntry](../models/logentry.md)]                       | :heavy_check_mark:                                                   | N/A                                                                  |