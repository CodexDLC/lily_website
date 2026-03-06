"""
codex_tools.booking.interfaces
==============================
Contracts (Protocols) for interacting with the outside world.
The library relies only on these interfaces, not on concrete Django models.
"""

from datetime import date, datetime, time
from typing import Protocol


class ScheduleProvider(Protocol):
    """
    Interface for providing working schedules.
    The project must implement this interface (or pass appropriate functions).
    """

    def get_working_hours(self, master_id: str, target_date: date) -> tuple[time, time] | None:
        """Returns the (start, end) of a working day or None if it's a day off."""
        ...

    def get_break_interval(self, master_id: str, target_date: date) -> tuple[datetime, datetime] | None:
        """Returns the (start, end) of a break or None."""
        ...


class BusySlotsProvider(Protocol):
    """
    Interface for providing busy slots.
    """

    def get_busy_intervals(
        self, master_ids: list[str], target_date: date
    ) -> dict[str, list[tuple[datetime, datetime]]]:
        """
        Returns a dictionary {master_id: [(start, end), ...]} of busy times.
        This includes existing appointments, technical breaks, etc.
        """
        ...
