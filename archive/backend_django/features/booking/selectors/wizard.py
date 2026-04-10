import calendar
from datetime import date, timedelta
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
            Category.objects.filter(is_active=True, is_planned=False, is_available=True)
            .annotate(active_masters_count=Count("masters", filter=Q(masters__status=Master.STATUS_ACTIVE)))
            .filter(active_masters_count__gt=0)
            .order_by("order")
        )

    categories = get_cached_data("wizard_categories_cache_v2", fetch_categories)

    if not selected_category_slug and categories:
        selected_category_slug = categories[0].slug

    def fetch_services():
        if not selected_category_slug:
            return []
        return list(
            Service.objects.filter(
                category__slug=selected_category_slug, is_active=True, is_planned=False, is_available=True
            ).order_by("order")
        )

    services = get_cached_data(f"wizard_services_cache_{selected_category_slug}_v2", fetch_services)

    return {
        "categories": categories,
        "selected_category_slug": selected_category_slug,
        "services": services,
    }


def get_step_2_context(state: BookingState, view_data: dict[str, Any]) -> dict[str, Any] | None:
    """Context for Step 2: Calendar & Slots (master not yet selected — show all available slots)."""
    context = {}

    # 1. Get Service
    if not state.service_id:
        return None
    try:
        service = Service.objects.select_related("category").get(id=state.service_id)
        context["selected_service"] = service
    except Service.DoesNotExist:
        return None

    # 2. Get all active masters for this category (slot aggregation — "any" logic)
    masters_list = list(Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE))

    if not masters_list:
        return None

    context["master_id"] = "any"

    # 3. Date Strip (Horizontal list for mobile)
    context["date_strip"] = _get_date_strip(days=14)

    # 4. Calendar Grid (Full grid for desktop/modal)
    today = timezone.now().date()
    try:
        year = int(view_data.get("year", today.year))
        month = int(view_data.get("month", today.month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    def fetch_calendar():
        return _get_calendar_grid(year, month)

    context.update(get_cached_data(f"calendar_grid_cache_{year}_{month}", fetch_calendar))

    # 5. Slots (DYNAMIC)
    if state.selected_date and service and masters_list:
        context["selected_date_obj"] = state.selected_date

        slot_service = SlotService()
        slots = slot_service.get_available_slots(
            masters=masters_list, date_obj=state.selected_date, duration_minutes=service.duration
        )
        context["available_slots"] = slots
        context["no_slots_available"] = len(slots) == 0

    return context


def get_step_3_context(state: BookingState) -> dict[str, Any] | None:
    """Context for Step 3: Masters available at the selected date & time slot. NOT cached (dynamic)."""
    if not (state.service_id and state.selected_date and state.selected_time):
        return None

    try:
        service = Service.objects.select_related("category").get(id=state.service_id)
    except Service.DoesNotExist:
        return None

    # Parse selected datetime
    from datetime import datetime as dt

    try:
        naive_dt = dt.strptime(f"{state.selected_date.isoformat()} {state.selected_time}", "%Y-%m-%d %H:%M")
        start_dt = timezone.make_aware(naive_dt)
    except (ValueError, TypeError):
        return None

    # All active public masters for this category
    candidates = list(
        Master.objects.filter(
            categories=service.category,
            status=Master.STATUS_ACTIVE,
            is_public=True,
        ).order_by("order")
    )

    # Filter 1: works on this weekday
    weekday = state.selected_date.weekday()
    candidates = [m for m in candidates if weekday in (m.work_days or [])]

    # Filter 2: no day-off on this date
    from features.booking.models.master_day_off import MasterDayOff

    day_off_ids = set(
        MasterDayOff.objects.filter(master__in=candidates, date=state.selected_date).values_list("master_id", flat=True)
    )
    candidates = [m for m in candidates if m.id not in day_off_ids]

    # Filter 3: slot is not already booked (best-effort for UI; final check is in BookingService)
    from features.booking.services.booking import BookingService

    available_masters = [
        m for m in candidates if BookingService._is_slot_still_available(m, start_dt, service.duration)
    ]

    # Check if ANY master (incl. non-public "any pool") is free at this slot
    # Used to auto-skip step 3 when only visiting/anonymous masters are available
    all_active = list(Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE))
    all_active = [m for m in all_active if weekday in (m.work_days or [])]
    all_active = [m for m in all_active if m.id not in day_off_ids]
    has_any_masters = any(BookingService._is_slot_still_available(m, start_dt, service.duration) for m in all_active)

    return {
        "available_masters": available_masters,
        "has_any_masters": has_any_masters,
        "selected_service": service,
        "selected_date": state.selected_date,
        "selected_time": state.selected_time,
        "service_id": state.service_id,
    }


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
        {"number": "2", "title": _("Termin"), "active": False, "completed": False},
        {"number": "3", "title": _("Experte"), "active": False, "completed": False},
        {"number": "4", "title": _("Bestätigung"), "active": False, "completed": False},
    ]
    for step in steps:
        step_number = int(step["number"])
        step["active"] = step_number == current_step
        step["completed"] = step_number < current_step
    return steps


def _get_date_strip(days: int = 14) -> list[dict[str, Any]]:
    """Generates a list of dates starting from today."""
    strip = []
    today = timezone.now().date()

    # German weekday names (short)
    weekdays = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    for i in range(days):
        current = today + timedelta(days=i)
        # Skip Sundays (optional, depends on business logic)
        status = "active"
        if current.weekday() == 6:
            status = "disabled"

        strip.append(
            {
                "date": current.isoformat(),
                "day_num": current.day,
                "weekday": weekdays[current.weekday()],
                "status": status,
                "is_today": i == 0,
            }
        )
    return strip


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
