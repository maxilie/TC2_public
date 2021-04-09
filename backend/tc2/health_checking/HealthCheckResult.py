from datetime import datetime
from typing import List, Dict


class HealthCheckResult:
    """Contains the status of a health check (passing or failing) and accompanying debug messages."""

    passing: bool
    debug_messages: List[str]
    last_updated: datetime

    def __init__(self, passing: bool, debug_messages: List[str], moment: datetime) -> None:
        self.passing = passing
        self.debug_messages = debug_messages
        self.last_updated = moment

    def to_json(self) -> Dict[str, any]:
        from tc2.util.date_util import DATE_TIME_FORMAT

        return {'status': 'PASSED' if self.passing else 'FAILED',
                'debug_messages': self.debug_messages,
                'last_updated': self.last_updated.strftime(DATE_TIME_FORMAT)}
