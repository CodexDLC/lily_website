import calendar
from datetime import date
from typing import Any, TypedDict

from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext as _
from features.booking.dto import BookingState
from features.booking.models.master import Master
from features.booking.services.slots import SlotService
from features.main.models.category import Category
from features.main.models.service import Service
from holidays.countries import Germany


class StepperStep(TypedDict):
    number: str
    title: str
    active: bool
    completed: bool


def get_step_1_context(state: BookingState) -> dict[str, Any]:
    """Context for Step 1: Services & Categories."""
    selected_category_slug = state.category_slug

    categories = (
        Category.objects.filter(is_active=True)
        .annotate(active_masters_count=Count("masters", filter=Q(masters__status=Master.STATUS_ACTIVE)))
        .filter(active_masters_count__gt=0)
        .order_by("order")
    )

    if not selected_category_slug and categories.exists():
        selected_category_slug = categories.first().slug

    services = []
    if selected_category_slug:
        services = Service.objects.filter(category__slug=selected_category_slug, is_active=True).order_by("order")

    return {
        "categories": categories,
        "selected_category_slug": selected_category_slug,
        "services": services,
    }


def get_step_2_context(state: BookingState) -> dict[str, Any] | None:
    """Context for Step 2: Masters."""
    if not state.service_id:
        return None

    try:
        service = Service.objects.get(id=state.service_id)
    except Service.DoesNotExist:
        return None

    masters = Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE).order_by("order")

    return {
        "selected_service": service,
        "masters": masters,
        "service_id": state.service_id,
    }


def get_step_3_context(state: BookingState, view_data: dict[str, Any]) -> dict[str, Any] | None:
    """Context for Step 3: Calendar & Slots."""
    context = {}

    # 1. Get Objects (Safe retrieval)
    service = None
    if state.service_id:
        try:
            service = Service.objects.get(id=state.service_id)
            context["selected_service"] = service
        except Service.DoesNotExist:
            return None
    else:
        return None  # Cannot proceed without service

    masters_list = []
    if state.master_id:
        if state.master_id == "any":
            masters_list = list(Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE))
        else:
            try:
                master = Master.objects.get(id=state.master_id)
                context["selected_master"] = master
                masters_list = [master]
            except (Master.DoesNotExist, ValueError):
                return None
    else:
        return None  # Cannot proceed without master

    # 2. Calendar Grid
    today = timezone.now().date()
    try:
        year = int(view_data.get("year", today.year))
        month = int(view_data.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    context.update(_get_calendar_grid(year, month))

    # 3. Slots (if date selected)
    if state.selected_date and service and masters_list:
        context["selected_date_obj"] = state.selected_date

        slot_service = SlotService()
        slots = slot_service.get_available_slots(
            masters=masters_list, date_obj=state.selected_date, duration_minutes=service.duration
        )
        context["available_slots"] = slots
        # Add flag if no slots available for selected date
        context["no_slots_available"] = len(slots) == 0

    return context


def get_step_4_context(state: BookingState) -> dict[str, Any] | None:
    """Context for Step 4: Confirmation."""
    if not state.service_id or not state.selected_date or not state.selected_time:
        return None

    context = {}
    try:
        context["selected_service"] = Service.objects.get(id=state.service_id)
        if state.master_id and state.master_id != "any":
            context["selected_master"] = Master.objects.get(id=state.master_id)

        context["selected_date"] = state.selected_date
        context["selected_time"] = state.selected_time
    except (Service.DoesNotExist, Master.DoesNotExist):
        return None

    return context


def get_stepper_context(current_step: int) -> list[StepperStep]:
    """Returns stepper state."""
    steps: list[StepperStep] = [
        {"number": "1", "title": _("Leistung"), "active": False, "completed": False},
        {"number": "2", "title": _("Experте"), "active": False, "completed": False},
        {"number": "3", "title": _("Termin"), "active": False, "completed": False},
        {"number": "4", "title": _("Bestätigung"), "active": False, "completed": False},
    ]
    for step in steps:
        step_number = int(step["number"])
        step["active"] = step_number == current_step
        step["completed"] = step_number < current_step
    return steps


def _get_calendar_grid(year: int, month: int) -> dict[str, Any]:
    """Helper to generate calendar matrix."""
    de_holidays = Germany(subdiv="ST", years=year)
    cal = calendar.Calendar(firstweekday=0)
    matrix = cal.monthdayscalendar(year, month)

    days_list = []
    today = timezone.now().date()

    for week in matrix:
        for day_num in week:
            if day_num == 0:
                days_list.append({"num": "", "status": "empty", "title": ""})
                continue

            current_date = date(year, month, day_num)
            status = "active"
            title = ""

            if current_date < today or current_date.weekday() == 6:
                status = "disabled"
            elif current_date in de_holidays:
                status = "holiday"
                title = de_holidays.get(current_date)

            days_list.append({"num": str(day_num), "status": status, "title": title, "date": current_date.isoformat()})

    # Fix for month name translation if needed, but keeping it simple for now
    month_name = date(year, month, 1).strftime("%B %Y")

    return {"calendar_days": days_list, "month_label": month_name, "current_year": year, "current_month": month}
