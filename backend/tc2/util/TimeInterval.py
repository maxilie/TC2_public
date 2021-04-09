import math
from datetime import timedelta, time, datetime
from typing import Union, Optional

from tc2.log.LogFeed import LogFeed, LogLevel


class TimeInterval:
    """Defines a possibly discontinuous interval of time as the union of continuous sub-intervals."""

    def __init__(self, logfeed: Optional[LogFeed], start1: time, end1: time, *args) -> None:
        """
        :param args: an even number of datetime.time objects ascending chronologically
                     e.x. (time(10, 0), time (10, 45))
        """
        self.logfeed: Optional[LogFeed] = logfeed

        self.sub_intervals = [ContinuousTimeInterval(start1, end1)]

        if len(args) == 0:
            return

        start_time = None
        for t in args:
            if start_time is None:
                start_time = t
            else:
                end_time = t
                sub_interval = ContinuousTimeInterval(start_time, end_time)
                if start_time >= end_time:
                    logfeed.log(LogLevel.ERROR, 'INVALID CONTINUOUS TIME INTERVAL (tried to cross midnight): {0}'
                                .format(sub_interval.pretty_print()))
                self.sub_intervals.append(sub_interval)
                # Reset variable so we can find the start of the next sub-interval
                start_time = None

    def contains_interval(self, interval: 'TimeInterval') -> bool:
        """
        :return: True if the given interval is contained in this time interval
        """
        # Check each sub-interval in question
        for sub_interval in self.sub_intervals:
            is_contained = False

            # Search each of this TimeInterval's sub-intervals for sub-interval
            for container_interval in self.sub_intervals:
                if datetime.combine(datetime.today(), container_interval.start_time) \
                        <= datetime.combine(datetime.today(), sub_interval.start_time) \
                        and datetime.combine(datetime.today(), container_interval.end_time) \
                        >= datetime.combine(datetime.today(), sub_interval.end_time):
                    is_contained = True
                    break

            if not is_contained:
                return False

        # Return true once all container sub-intervals are found
        return True

    def contains_time(self, t: Union[time, datetime]) -> bool:
        """
        :return: True if the given time falls within this time interval
        """
        # If user chose to input a datetime, convert it to a time
        if isinstance(t, datetime):
            t = t.time()

        # Search each continuous sub-interval for the time
        for continuous_interval in self.sub_intervals:
            if continuous_interval.start_time <= t <= continuous_interval.end_time:
                if self.logfeed is not None:
                    # self.logfeed.log(LogLevel.DEBUG, 't={0}:{1}:{2} contained in {3}'
                    #                 .format(t.hour, t.minute, t.second, continuous_interval.pretty_print()))
                    pass
                return True
            else:
                if self.logfeed is not None:
                    # self.logfeed.log(LogLevel.DEBUG, 't={0}:{1}:{2} NOT contained in {3}'
                    #                 .format(t.hour, t.minute, t.second, continuous_interval.pretty_print()))
                    pass
        if self.logfeed is not None:
            # self.logfeed.log(LogLevel.DEBUG, 't={0}:{1}:{2} not found anywhere in {3}'
            #                 .format(t.hour, t.minute, t.second, self.pretty_print()))
            pass
        return False

    def will_contain_in(self, t: Union[time, datetime]) -> timedelta:
        """
        :return: the wait until this interval will contain the given time,
                 or 0 if the given time is already contained in the interval
        """
        if isinstance(t, datetime):
            t = t.time()
        if self.contains_time(t):
            return timedelta(hours=0, minutes=0, seconds=0)

        smallest_delta = None
        for continuous_interval in self.sub_intervals:
            if continuous_interval.start_time > t:
                delta = datetime.combine(datetime.today(), continuous_interval.start_time) - \
                        datetime.combine(datetime.today(), t)
            else:
                delta = datetime.combine(datetime.today(), continuous_interval.start_time) + timedelta(days=1) - \
                        datetime.combine(datetime.today(), t)
            if smallest_delta is None or delta < smallest_delta:
                smallest_delta = delta
        return smallest_delta

    def will_contain_for(self, t: Union[time, datetime]) -> timedelta:
        """
        :return: the wait until this interval will no longer contain the given time,
                 or 0 if the given time is already not contained in the interval
        """
        if isinstance(t, datetime):
            t = t.time()

        if not self.contains_time(t):
            return timedelta(hours=0, minutes=0, seconds=0)

        largest_delta = None
        for continuous_interval in self.sub_intervals:
            if continuous_interval.start_time > t:
                continue
            delta = datetime.combine(datetime.today(), continuous_interval.end_time) - \
                    datetime.combine(datetime.today(), t)
            if largest_delta is None or delta > largest_delta:
                largest_delta = delta
        return largest_delta

    def get_start_time(self) -> time:
        return self.sub_intervals[0].start_time

    def get_end_time(self) -> time:
        return self.sub_intervals[-1].end_time

    def total_seconds(self) -> int:
        secs = 0
        for sub_interval in self.sub_intervals:
            secs += (datetime.combine(datetime.today(), sub_interval.end_time)
                     - datetime.combine(datetime.today(), sub_interval.start_time)).total_seconds()
        return math.ceil(secs)

    def total_mins(self) -> int:
        return math.ceil(self.total_seconds() / 60.0)

    def pretty_print(self) -> str:
        """
        Returns the (possibly discontinuous) time interval like so:
        [[hh:mm:ss, hh:mm:ss], ..., [hh:mm:ss, hh:mm:ss]].
        """
        pretty_str = ''
        for continuous_interval in self.sub_intervals:
            pretty_str = pretty_str + ', {0}'.format(continuous_interval.pretty_print())
        return '[' + pretty_str[2:] + ']'


class ContinuousTimeInterval:
    """
    A continuous interval of time defined by start_time and end_time.
    """

    def __init__(self, start_time: time, end_time: time) -> None:
        self.start_time = start_time
        self.end_time = end_time

    def sub_interval(self, start_pct: float, end_pct: float) -> 'ContinuousTimeInterval':
        """
        :param start_pct: a number between 0 and 1
        :param end_pct: a number between 0 and 1 (must be greater than start_pct)
        :return: a sub-interval (i.e. this interval is [0, 1] and the output is [start_pct*t, end_pct*t]
        """
        if not 0 <= start_pct < end_pct <= 1:
            raise ValueError('sub_interval of ContinuousTimeInterval must be [a,b] where 0 <= a < b <= 1')

        length = self.length()

        return ContinuousTimeInterval(start_time=(datetime.combine(datetime.now().date(), self.start_time)
                                                  + timedelta(seconds=length * start_pct)).time(),
                                      end_time=(datetime.combine(datetime.now().date(), self.start_time)
                                                + timedelta(seconds=length * end_pct)).time())

    def length(self) -> int:
        """Returns the interval's length in seconds."""
        return int((datetime.combine(datetime.now().date(), self.end_time) -
                    datetime.combine(datetime.now().date(), self.start_time)).total_seconds())

    def pretty_print(self) -> str:
        """Returns the (continuous) time interval like so: [hh:mm:ss, hh:mm:ss]."""
        return '[{0}: {1}:{2}, {3}: {4}:{5}]' \
            .format(self.start_time.hour, self.start_time.minute, self.start_time.second, self.end_time.hour,
                    self.end_time.minute, self.end_time.second)
