import calendar
from datetime import date
from typing import Any, TypedDict

from core.cache import get_cached_data
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
    """Context for Step 1: Services & Categories. Cached."""
    selected_category_slug = state.category_slug

    def fetch_categories():
        return list(
            Category.objects.filter(is_active=True)
            .annotate(active_masters_count=Count("masters", filter=Q(masters__status=Master.STATUS_ACTIVE)))
            .filter(active_masters_count__gt=0)
            .order_by("order")
        )

    categories = get_cached_data("wizard_categories_cache", fetch_categories)

    if not selected_category_slug and categories:
        selected_category_slug = categories[0].slug

    def fetch_services():
        if not selected_category_slug:
            return []
        return list(Service.objects.filter(category__slug=selected_category_slug, is_active=True).order_by("order"))

    services = get_cached_data(f"wizard_services_cache_{selected_category_slug}", fetch_services)

    return {
        "categories": categories,
        "selected_category_slug": selected_category_slug,
        "services": services,
    }


def get_step_2_context(state: BookingState) -> dict[str, Any] | None:
    """Context for Step 2: Masters. Cached."""
    if not state.service_id:
        return None

    def fetch():
        try:
            service = Service.objects.get(id=state.service_id)
            masters = list(
                Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE).order_by("order")
            )
            return {"selected_service": service, "masters": masters, "service_id": state.service_id}
        except Service.DoesNotExist:
            return None

    return get_cached_data(f"wizard_step_2_cache_{state.service_id}", fetch)


def get_step_3_context(state: BookingState, view_data: dict[str, Any]) -> dict[str, Any] | None:
    """Context for Step 3: Calendar & Slots."""
    context = {}

    # 1. Get Service
    if not state.service_id:
        return None
    try:
        service = Service.objects.get(id=state.service_id)
        context["selected_service"] = service
    except Service.DoesNotExist:
        return None

    # 2. Get Masters (Handle "any" or specific ID)
    masters_list = []
    master_id_val = state.master_id or "any"  # Default to any if not set
    context["master_id"] = master_id_val  # Pass raw value to template

    if master_id_val == "any":
        masters_list = list(Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE))
    else:
        try:
            master = Master.objects.get(id=master_id_val)
            context["selected_master"] = master
            masters_list = [master]
        except (Master.DoesNotExist, ValueError):
            # If specific master not found, fallback to "any" instead of returning None
            masters_list = list(Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE))
            context["master_id"] = "any"

    if not masters_list:
        return None

    # 3. Calendar Grid (Cached)
    today = timezone.now().date()
    try:
        year = int(view_data.get("year", today.year))
        month = int(view_data.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    def fetch_calendar():
        return _get_calendar_grid(year, month)

    context.update(get_cached_data(f"calendar_grid_cache_{year}_{month}", fetch_calendar))

    # 4. Slots (DYNAMIC)
    if state.selected_date and service and masters_list:
        context["selected_date_obj"] = state.selected_date

        slot_service = SlotService()
        slots = slot_service.get_available_slots(
            masters=masters_list, date_obj=state.selected_date, duration_minutes=service.duration
        )
        context["available_slots"] = slots
        context["no_slots_available"] = len(slots) == 0

    return context


def get_step_4_context(state: BookingState) -> dict[str, Any] | None:
    """Context for Step 4: Confirmation. Dynamic."""
    if not state.service_id or not state.selected_date or not state.selected_time:
        return None

    context = {}
    try:
        context["selected_service"] = Service.objects.get(id=state.service_id)
        if state.master_id and state.master_id != "any":
            context["selected_master"] = Master.objects.get(id=state.master_id)

        context["master_id"] = state.master_id or "any"
        context["selected_date"] = state.selected_date
        context["selected_time"] = state.selected_time
    except (Service.DoesNotExist, Master.DoesNotExist):
        return None

    return context


def get_stepper_context(current_step: int) -> list[StepperStep]:
    """Returns stepper state."""
    steps: list[StepperStep] = [
        {"number": "1", "title": _("Leistung"), "active": False, "completed": False},
        {"number": "2", "title": _("Experte"), "active": False, "completed": False},
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

    month_name = date(year, month, 1).strftime("%B %Y")

    return {"calendar_days": days_list, "month_label": month_name, "current_year": year, "current_month": month}
