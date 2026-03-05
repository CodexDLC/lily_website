"""
Selectors for V2 Booking Constructor.

Provide context data for the V2 wizard UI panels.
All functions are pure -- no side effects, no session writes.
"""

from datetime import date, timedelta

from core.logger import log
from django.utils import timezone
from features.booking.models import BookingSettings, Master, MasterDayOff
from features.booking.services.v2_booking_service import BookingV2Service
from features.main.models.category import Category
from features.main.models.service import Service


def get_services_panel_context() -> dict:
    """
    Context for the first panel: service selection.
    """
    categories = (
        Category.objects.prefetch_related("services")
        .filter(services__is_active=True)
        .distinct()
        .order_by("order", "title")
    )

    result = []
    for category in categories:
        services = [
            {
                "id": svc.id,
                "title": svc.title,
                "duration": svc.duration,
                "price": str(svc.price),
                "min_gap_after": getattr(svc, "min_gap_after_minutes", 0),
            }
            for svc in category.services.filter(is_active=True).order_by("title")
        ]
        if services:
            result.append(
                {
                    "id": category.id,
                    "title": category.title,
                    "services": services,
                }
            )

    return {"categories": result}


def get_calendar_panel_context(
    selected_service_ids: list[int],
    month: int | None = None,
    year: int | None = None,
    selected_date: date | None = None,
) -> dict:
    """
    Context for the calendar panel: which dates are available.
    """
    import calendar

    settings = BookingSettings.load()
    today = timezone.localdate()

    target_month: int = int(month) if month is not None else int(today.month)
    target_year: int = int(year) if year is not None else int(today.year)

    try:
        date(target_year, target_month, 1)
    except ValueError:
        target_month = int(today.month)
        target_year = int(today.year)

    max_date = today + timedelta(days=settings.default_max_advance_days)

    cal = calendar.Calendar(firstweekday=0)  # Monday first
    month_days = cal.itermonthdays(target_year, target_month)

    service_master_map: dict[int, list[tuple[int, list[int]]]] = {}
    services = Service.objects.filter(id__in=selected_service_ids).prefetch_related("category")
    for svc in services:
        masters = Master.objects.filter(categories=svc.category, status=Master.STATUS_ACTIVE).values_list(
            "id", "work_days"
        )
        service_master_map[svc.id] = list(masters)  # type: ignore

    month_day_offs = MasterDayOff.objects.filter(date__year=target_year, date__month=target_month).values_list(
        "master_id", "date"
    )
    day_off_map: dict[date, set[int]] = {}
    for mid, d in month_day_offs:
        if d not in day_off_map:
            day_off_map[d] = set()
        day_off_map[d].add(mid)

    calendar_days = []
    for day_num in month_days:
        if day_num == 0:
            calendar_days.append({"num": "", "status": "empty"})
            continue

        calc_date = date(target_year, target_month, day_num)
        weekday = calc_date.weekday()

        if calc_date < today or calc_date > max_date or weekday == 6:
            status = "disabled"
        else:
            is_possible = True
            for svc_id in selected_service_ids:
                masters_for_svc = service_master_map.get(svc_id, [])
                has_on_duty = False
                for mid, work_days in masters_for_svc:
                    if weekday in (work_days or []) and mid not in day_off_map.get(calc_date, set()):
                        has_on_duty = True
                        break
                if not has_on_duty:
                    is_possible = False
                    break

            status = "available" if is_possible else "no_slots"

        if selected_date and calc_date == selected_date:
            status = "active"

        calendar_days.append({"num": str(day_num), "status": status, "date": calc_date.isoformat()})

    month_names: dict[int, str] = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }

    category_slug = ""
    if selected_service_ids:
        first_svc = Service.objects.filter(id=selected_service_ids[0]).select_related("category").first()
        if first_svc and first_svc.category:
            category_slug = first_svc.category.slug

    return {
        "current_month": target_month,
        "current_year": target_year,
        "month_label": f"{month_names.get(target_month, '')} {target_year}",
        "calendar_days": calendar_days,
        "category_slug": category_slug,
    }


def get_slots_panel_context(
    selected_service_ids: list[int],
    selected_date: date,
    mode: str = "complex",
    master_selections: dict[int, str] | None = None,
    exclude_appointment_ids: list[int] | None = None,
) -> dict:
    """
    Context for the slot selection panel.
    """
    log.debug(
        "wizard_v2.get_slots_panel_context: service_ids={} date={} mode={} exclude={}",
        selected_service_ids,
        selected_date,
        mode,
        exclude_appointment_ids,
    )
    service = BookingV2Service()
    slots_map = service.get_available_slots(
        service_ids=selected_service_ids,
        target_date=selected_date,
        master_selections=master_selections,
        exclude_appointment_ids=exclude_appointment_ids,
    )

    slot_times = sorted(slots_map.keys())

    return {
        "date": selected_date.isoformat(),
        "date_display": selected_date.strftime("%d.%m.%Y"),
        "slots": slot_times,
        "has_slots": bool(slot_times),
        "mode": mode,
    }


def get_summary_context(
    selected_service_ids: list[int],
    selected_date: date,
    selected_time: str,
) -> dict:
    """
    Context for the confirmation (summary) panel.
    """
    services = Service.objects.filter(id__in=selected_service_ids)
    svc_map = {s.id: s for s in services}

    svc_list = []
    total_duration = 0
    total_price = 0

    for svc_id in selected_service_ids:
        svc = svc_map.get(svc_id)
        if not svc:
            continue
        svc_list.append(
            {
                "title": svc.title,
                "duration": svc.duration,
                "price": str(svc.price),
            }
        )
        total_duration += svc.duration
        total_price += svc.price

    return {
        "services": svc_list,
        "date_display": selected_date.strftime("%d.%m.%Y"),
        "time": selected_time,
        "total_duration": total_duration,
        "total_price": str(total_price),
    }
