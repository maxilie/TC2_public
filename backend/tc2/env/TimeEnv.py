from datetime import datetime, timedelta, date

from tc2.util.market_util import OPEN_TIME, CLOSE_TIME, calculate_holidays

HOLIDAYS = calculate_holidays()


class TimeEnv:
    """
    Allows the same code to run live or simulated by using the environment's time.
    """

    def __init__(self, moment: datetime) -> None:
        """
        :param moment: the environment's time upon creation (i.e. set to datetime.now() for live environment)
        """
        self.set_moment(moment)

    def set_moment(self, moment: datetime) -> None:
        """Moves the environment's perspective to the specified moment in time."""
        self.time_offset: timedelta = datetime.now() - moment

    def now(self) -> datetime:
        return datetime.now() - self.time_offset

    def is_open(self, moment: datetime = None) -> bool:
        """
        :param moment: leave blank to use environment's current time
        :return: whether the U.S. markets are open at the given moment
        """
        if not moment:
            moment = self.now()
        return self.is_mkt_day(moment.date()) and OPEN_TIME <= moment.time() < CLOSE_TIME

    def is_mkt_day(self, day: date = None) -> bool:
        """
        :param day: leave blank to use environment's current date
        :return: whether the U.S. markets are open on the given date
        """
        if not day:
            day = self.now().date()
        return day.weekday() != 5 and day.weekday() != 6 and day not in HOLIDAYS

    def get_prev_mkt_day(self, day: date = None) -> date:
        """
        :param day: leave blank to use environment's current date
        :return: the closest date, before the given date, on which U.S. markets are open
        """
        if not day:
            day = self.now().date()
        prev_day = day - timedelta(days=1)
        while not self.is_mkt_day(prev_day):
            prev_day -= timedelta(days=1)
        return prev_day

    def get_next_mkt_day(self, day: date = None) -> date:
        """
        :param day: leave blank to use environment's current date
        :return: the closest date, after the given date, on which U.S. markets are open
        """
        if not day:
            day = self.now().date()
        next_day = day + timedelta(days=1)
        while not self.is_mkt_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def get_secs_to_open(self, moment: datetime = None) -> int:
        """
        :param moment: leave blank to use environment's current date
        :return: the number of seconds until the markets open, or 0 if markets are open at the given moment
        """
        if not moment:
            moment = self.now()
        if self.is_open(moment):
            return True
        diff = datetime.combine(self.get_next_mkt_day(moment), OPEN_TIME) - moment
        return int(diff.total_seconds())

    def get_secs_to_close(self, moment: datetime = None) -> int:
        """
        :param moment: leave blank to use environment's current date
        :return: the number of seconds until the markets close, or 0 if markets are closed at the given moment
        """
        if not moment:
            moment = self.now()
        if not self.is_open(moment):
            return 0
        diff = datetime.combine(moment.date(), CLOSE_TIME) - moment
        return int(diff.total_seconds())
