# models/chronometer.py
"""
Minimal Chronometer class for ship time tracking.
Tracks total minutes since launch and formats for display.
"""

from constants import START_DATE_TIME


class Chronometer:
    """
    Simple ship chronometer.
    Starts at START_DATE_TIME and advances in minutes.
    """

    def __init__(self):
        start_year, start_month, start_day, start_hour, start_minute = START_DATE_TIME
        # Convert start date to total minutes since "epoch zero"
        self.total_minutes = self._date_to_minutes(start_year, start_month, start_day, start_hour, start_minute)

    @staticmethod
    def _date_to_minutes(year: int, month: int, day: int, hour: int, minute: int) -> int:
        """Convert date/time to total minutes since year 0 (simple, no leap years)."""
        # Simple calendar: 30 days per month, 360 days per year
        days = (year * 360) + ((month - 1) * 30) + (day - 1)
        return (days * 24 * 60) + (hour * 60) + minute

    @staticmethod
    def _minutes_to_date(total_minutes: int) -> tuple[int, int, int, int, int]:
        """Convert total minutes back to (year, month, day, hour, minute)."""
        minutes_in_day = 24 * 60
        days = total_minutes // minutes_in_day
        minutes_left = total_minutes % minutes_in_day

        year = days // 360
        days_in_year = days % 360
        month = (days_in_year // 30) + 1
        day = (days_in_year % 30) + 1

        hour = minutes_left // 60
        minute = minutes_left % 60

        return year, month, day, hour, minute

    def advance(self, minutes: int) -> None:
        """Advance ship time by given minutes."""
        self.total_minutes += minutes

    def get_formatted(self) -> str:
        """Return formatted string: '01-06-2145  15:37'"""
        year, month, day, hour, minute = self._minutes_to_date(self.total_minutes)
        return f"{day:02d}-{month:02d}-{year:04d}  {hour:02d}:{minute:02d}"