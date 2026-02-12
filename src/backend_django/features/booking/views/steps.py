from typing import Any, cast

from django.http import HttpRequest
from django.utils import timezone
from features.booking.dto import BookingState
from features.booking.selectors import wizard as wizard_selectors


class BaseStep:
    """Base class for Wizard Steps."""

    template_name = ""

    def __init__(self, state: BookingState, request: HttpRequest):
        self.state = state
        self.request = request

    def get_context(self) -> dict[str, Any] | None:
        """Returns context data for the template."""
        return {}


class ServiceStep(BaseStep):
    template_name = "booking/steps/step_1_services_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        return cast("dict[str, Any] | None", wizard_selectors.get_step_1_context(self.state))


class MasterStep(BaseStep):
    template_name = "booking/steps/step_2_masters_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        return cast("dict[str, Any] | None", wizard_selectors.get_step_2_context(self.state))


class CalendarStep(BaseStep):
    template_name = "booking/steps/step_3_calendar_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        # View-specific params (year/month) are not part of the core state
        today = timezone.now().date()
        view_data = {
            "year": self.request.GET.get("year", today.year),
            "month": self.request.GET.get("month", today.month),
        }
        return cast("dict[str, Any] | None", wizard_selectors.get_step_3_context(self.state, view_data))


class ConfirmStep(BaseStep):
    template_name = "booking/steps/step_4_confirm_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        return cast("dict[str, Any] | None", wizard_selectors.get_step_4_context(self.state))
