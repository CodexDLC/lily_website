from datetime import date

from codex_tools.codex_calendar.engine import CalendarEngine
from django.utils import timezone


class CalendarService:
    """
    Django-wrapper for the pure CalendarEngine.
    """

    @staticmethod
    def get_calendar_month_data(year: int, month: int, selected_date: date | None = None):
        """
        Generates a list of days for a calendar grid with statuses.
        Uses codex_tools.codex_calendar.engine for core logic.
        """
        today = timezone.localdate()

        # Core logic from codex_tools
        days = CalendarEngine.get_month_matrix(
            year=year,
            month=month,
            today=today,
            selected_date=selected_date,
            holidays_subdiv="ST",  # Saxony-Anhalt
        )

        # Label from codex_tools
        month_label = CalendarEngine.get_month_label(year, month, locale="ru")

        return {"days": days, "month_label": month_label}
