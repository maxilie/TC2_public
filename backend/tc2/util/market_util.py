from datetime import datetime, timedelta, date, time
from typing import List

from tc2.util.TimeInterval import TimeInterval

"""Times"""
OPEN_TIME = time(hour=9, minute=30)
CLOSE_TIME = time(hour=16, minute=0)

"""Time durations in seconds"""
FOR_1_MIN = 60
FOR_15_MINS = FOR_1_MIN * 15
FOR_1_HR = FOR_1_MIN * 60
FOR_24_HRS = FOR_1_HR * 24
# How long the markets are open for on a regular market day, in seconds
OPEN_DURATION = FOR_1_HR * 6.5
# How long the markets are closed for on a regular market day, in seconds
CLOSED_DURATION = FOR_24_HRS - OPEN_DURATION
# How many minutes to wait after markets close before the program trains its analysis models
MODEL_FEED_DELAY = FOR_15_MINS

"""Time intervals"""
ENTIRE_DAY = TimeInterval(None, OPEN_TIME, CLOSE_TIME)
FIRST_45_MINS = TimeInterval(None, OPEN_TIME,
                             (datetime.combine(datetime.today(), OPEN_TIME) + timedelta(minutes=45)).time())


def calculate_holidays() -> List[date]:
    """Calculates market holidays from 2015 - 2030"""
    holidays = []
    for year in range(2015, 2030):
        holidays.extend(_get_holidays_in_year(year))
    return holidays


def _get_holidays_in_year(year: int) -> List[date]:
    """Calculates all the market holidays for the given year."""
    return [_new_years_day_observed(year),
            _mlk_day_observed(year),
            _presidents_day_observed(year),
            _good_friday_observed(year),
            _memorial_day_observed(year),
            _independence_day_observed(year),
            _day_before_independence_day_observed(year),
            _labor_day_observed(year),
            _thanksgiving_observed(year),
            _day_after_thanksgiving_observed(year),
            _christmas_observed(year),
            _christmas_eve_observed(year)]


def _new_years_day_observed(year: int) -> date:
    """Observed on the weekday nearest to January 1st."""
    day = date(year=year, month=1, day=1)
    if day.weekday() == 5:
        # If Saturday, observe on the preceding friday
        return day - timedelta(days=1)
    elif day.weekday() == 6:
        # If Sunday, observe on the proceeding monday
        return day + timedelta(days=1)
    else:
        # If a weekday, observe on that day
        return day


def _mlk_day_observed(year: int) -> date:
    """Observed on the third Monday in January."""
    day = date(year=year, month=1, day=1)
    mondays = 0
    while True:
        if day.weekday() == 0:
            mondays += 1
            if mondays == 3:
                return day
            day += timedelta(days=7)
        else:
            day += timedelta(days=1)


def _presidents_day_observed(year: int) -> date:
    """Observed on the third Monday in February."""
    day = date(year=year, month=2, day=1)
    mondays = 0
    while True:
        if day.weekday() == 0:
            mondays += 1
            if mondays == 3:
                return day
            day += timedelta(days=7)
        else:
            day += timedelta(days=1)


def _good_friday_observed(year: int) -> date:
    """Observed on the Friday before Easter Sunday."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day_of_month = f % 31 + 1
    return date(year, month, day_of_month) - timedelta(days=2)


def _memorial_day_observed(year: int) -> date:
    """Observed on the last Monday in May."""
    day = date(year=year, month=5, day=31)
    while True:
        if day.weekday() == 0:
            return day
        else:
            day -= timedelta(days=1)


def _independence_day_observed(year: int) -> date:
    """Observed on the weekday nearest to July 4th."""
    day = date(year=year, month=7, day=4)
    if day.weekday() == 5:
        # If Saturday, observe on the preceding friday
        return day - timedelta(days=1)
    elif day.weekday() == 6:
        # If Sunday, observe on the following monday
        return day + timedelta(days=1)
    else:
        # If a weekday, observe on that day
        return day


def _day_before_independence_day_observed(year: int) -> date:
    """Observed on July 3rd if independence day falls on a weekend."""
    return date(year=year, month=7, day=3)


def _labor_day_observed(year: int) -> date:
    """Observed on the first Monday in September."""
    day = date(year=year, month=9, day=1)
    while True:
        if day.weekday() == 0:
            return day
        else:
            day += timedelta(days=1)


def _thanksgiving_observed(year: int) -> date:
    """Observed on the fourth Thursday in November."""
    day = date(year=year, month=11, day=1)
    thursdays = 0
    while True:
        if day.weekday() == 3:
            thursdays += 1
            if thursdays == 4:
                return day
            day += timedelta(days=7)
        else:
            day += timedelta(days=1)


def _day_after_thanksgiving_observed(year: int) -> date:
    """Observed on the day after Thanksgiving (always a Friday)."""
    return _thanksgiving_observed(year) + timedelta(days=1)


def _christmas_observed(year: int) -> date:
    """Observed on the weekday nearest to December 25th."""
    day = date(year=year, month=12, day=25)
    if day.weekday() == 5:
        # If Saturday, observe on the preceding friday
        return day - timedelta(days=1)
    elif day.weekday() == 6:
        # If Sunday, observe on the proceeding monday
        return day + timedelta(days=1)
    else:
        return day


def _christmas_eve_observed(year: int) -> date:
    """Observed on December 24th, regardless of when Christmas is observed."""
    return date(year=year, month=12, day=24)
