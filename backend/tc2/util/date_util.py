from datetime import time, date, datetime

# The formats used by this program to represent date, time, and datetime objects as strings
DATE_FORMAT = '%Y/%m/%d'
DATE_TIME_FORMAT = '%Y/%m/%d_%H:%M:%S'
TIME_FORMAT = '%H:%M:%S'

ENCODE_TIME = time(hour=0, minute=0, second=0)


def date_to_datetime(day: date) -> datetime:
    """Converts a date to a datetime so mongo can store it."""
    return datetime.combine(day, ENCODE_TIME)


def datetime_to_date(day_with_time: datetime) -> date:
    """Converts a datetime stored in mongo to a date object."""
    return day_with_time.date()
