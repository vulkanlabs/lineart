import datetime


def validate_date_range(
    start_date: datetime.date | None,
    end_date: datetime.date | None,
):
    if start_date is None:
        start_date = datetime.date.today() - datetime.timedelta(days=30)
    if end_date is None:
        end_date = datetime.date.today()
    return start_date, end_date
