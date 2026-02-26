from typing import Any, cast

from core.logger import log
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
        log.debug(f"View: BookingStep | Action: GetContext | step={self.state.step} | template={self.template_name}")
        return {}


class ServiceStep(BaseStep):
    template_name = "booking/steps/step_1_services_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        log.debug(f"View: ServiceStep | Action: LoadContext | category={self.state.category_slug}")
        return cast("dict[str, Any] | None", wizard_selectors.get_step_1_context(self.state))


class MasterStep(BaseStep):
    template_name = "booking/steps/step_2_masters_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        log.debug(f"View: MasterStep | Action: LoadContext | service_id={self.state.service_id}")
        return cast("dict[str, Any] | None", wizard_selectors.get_step_2_context(self.state))


class CalendarStep(BaseStep):
    template_name = "booking/steps/step_3_calendar_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        # View-specific params (year/month) are not part of the core state
        today = timezone.now().date()
        year = self.request.GET.get("year", today.year)
        month = self.request.GET.get("month", today.month)

        log.debug(
            f"View: CalendarStep | Action: LoadContext | master_id={self.state.master_id} | year={year} | month={month}"
        )

        view_data = {
            "year": year,
            "month": month,
        }
        return cast("dict[str, Any] | None", wizard_selectors.get_step_3_context(self.state, view_data))


class ConfirmStep(BaseStep):
    template_name = "booking/steps/step_4_confirm_mock.html"

    def get_context(self) -> dict[str, Any] | None:
        log.debug(
            f"View: ConfirmStep | Action: LoadContext | date={self.state.selected_date} | time={self.state.selected_time}"
        )
        return cast("dict[str, Any] | None", wizard_selectors.get_step_4_context(self.state))
