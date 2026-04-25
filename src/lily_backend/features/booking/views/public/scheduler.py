import calendar
import contextlib
import datetime

from core.logger import logger
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import formats, timezone
from django.views import View

from features.booking.booking_settings import BookingSettings
from features.booking.dto.public_cart import get_cart, save_cart
from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService


def _month_index(value: datetime.date) -> int:
    return value.year * 12 + value.month


def _resolve_service_scope(request: HttpRequest) -> tuple[list[int], int | None]:
    cart = get_cart(request)
    service_id_raw = request.GET.get("service_id", "").strip()
    if service_id_raw.isdigit():
        service_id = int(service_id_raw)
        if cart.has(service_id):
            return [service_id], service_id
    return cart.service_ids(), None


def _get_selected_date(request: HttpRequest, *, scoped_service_id: int | None) -> datetime.date | None:
    cart = get_cart(request)
    selected_date_raw = cart.date or ""
    if scoped_service_id is not None:
        selected_date_raw = next(
            (item.date or "" for item in cart.items if item.service_id == scoped_service_id),
            "",
        )
    if not selected_date_raw:
        return None
    with contextlib.suppress(ValueError):
        return datetime.date.fromisoformat(selected_date_raw)
    return None


def _build_calendar_grid(
    *,
    year: int,
    month: int,
    today: datetime.date,
    selected_date: datetime.date | None,
    min_date: datetime.date,
    max_date: datetime.date,
    available_dates: set[str],
) -> list[dict[str, object]]:
    grid: list[dict[str, object]] = []
    month_calendar = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)

    for week in month_calendar:
        for day in week:
            in_month = day.month == month
            iso = day.isoformat() if in_month else ""
            in_range = in_month and min_date <= day <= max_date
            is_available = bool(iso) and iso in available_dates and in_range
            grid.append(
                {
                    "num": str(day.day) if in_month else "0",
                    "date": iso,
                    "is_today": in_month and day == today,
                    "is_past": in_month and day < today,
                    "is_available": is_available,
                    "is_active": in_month and selected_date == day,
                    "is_out_of_range": in_month and not in_range,
                }
            )
    return grid


class SchedulerCalendarView(View):
    """GET ?year=&month= → calendar grid fragment bound to actual available dates."""

    def get(self, request: HttpRequest) -> HttpResponse:
        cart = get_cart(request)
        settings = BookingSettings.load()
        availability = CabinetBookingAvailabilityService(audience="public")
        today = timezone.localdate()
        service_ids, scoped_service_id = _resolve_service_scope(request)
        selected_date = _get_selected_date(request, scoped_service_id=scoped_service_id)

        min_date = today + datetime.timedelta(days=1 if settings.book_only_from_next_day else 0)
        max_date = today + datetime.timedelta(days=max(settings.max_advance_days - 1, 0))
        base_month = selected_date or min_date

        try:
            requested_year = int(request.GET.get("year", base_month.year))
            requested_month = int(request.GET.get("month", base_month.month))
            requested_date = datetime.date(requested_year, requested_month, 1)
        except ValueError:
            requested_date = base_month.replace(day=1)

        min_month = min_date.replace(day=1)
        max_month = max_date.replace(day=1)
        if _month_index(requested_date) < _month_index(min_month):
            requested_date = min_month
        if _month_index(requested_date) > _month_index(max_month):
            requested_date = max_month

        available_dates = availability.get_available_dates(
            start_date=today,
            horizon=settings.max_advance_days,
            service_ids=service_ids,
        )
        calendar_data = _build_calendar_grid(
            year=requested_date.year,
            month=requested_date.month,
            today=today,
            selected_date=selected_date,
            min_date=min_date,
            max_date=max_date,
            available_dates=available_dates,
        )

        prev_date = (requested_date.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        next_date = (requested_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        can_go_prev = _month_index(prev_date) >= _month_index(min_month)
        can_go_next = _month_index(next_date) <= _month_index(max_month)

        logger.debug(
            "Public calendar rendered: service_ids={} scoped_service_id={} month={} available_dates={} selected_date={}",
            service_ids,
            scoped_service_id,
            requested_date.strftime("%Y-%m"),
            sorted(available_dates),
            selected_date,
        )
        calendar_target_id = f"bk-calendar-{scoped_service_id}" if scoped_service_id is not None else "bk-calendar"

        return render(
            request,
            "features/booking/partials/calendar.html",
            {
                "calendar_data": calendar_data,
                "month_label": formats.date_format(requested_date, "F Y"),
                "year": requested_date.year,
                "month": requested_date.month,
                "prev_month": prev_date.month,
                "prev_year": prev_date.year,
                "next_month": next_date.month,
                "next_year": next_date.year,
                "can_go_prev": can_go_prev,
                "can_go_next": can_go_next,
                "cart": cart,
                "service_id": scoped_service_id,
                "calendar_target_id": calendar_target_id,
            },
        )


class SchedulerSlotsView(View):
    """GET ?date=YYYY-MM-DD → available time slots for the scoped services on that date."""

    def get(self, request: HttpRequest) -> HttpResponse:
        date_str = request.GET.get("date", "")
        try:
            target_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return HttpResponse(status=400)

        cart = get_cart(request)
        if cart.is_empty():
            return HttpResponse(status=400)

        service_ids, scoped_service_id = _resolve_service_scope(request)
        if not service_ids:
            return HttpResponse(status=400)

        availability = CabinetBookingAvailabilityService(audience="public")
        slots = availability.get_slots(
            booking_date=target_date.isoformat(),
            service_ids=service_ids,
        )
        selected_time = cart.time or ""
        if scoped_service_id is not None:
            selected_time = next(
                (item.time or "" for item in cart.items if item.service_id == scoped_service_id),
                "",
            )

        logger.debug(
            "Public slots rendered: date={} service_ids={} scoped_service_id={} slots={}",
            target_date,
            service_ids,
            scoped_service_id,
            slots,
        )

        return render(
            request,
            "features/booking/partials/slots_panel.html",
            {
                "slots": slots,
                "date": target_date,
                "cart": cart,
                "selected_time": selected_time,
                "service_id": scoped_service_id,
            },
        )


class SchedulerSlotsItemView(View):
    """GET ?service_id=&date=YYYY-MM-DD → slots for a single cart item (multi-day mode)."""

    def get(self, request: HttpRequest) -> HttpResponse:
        return SchedulerSlotsView().get(request)


class SchedulerConfirmTimeView(View):
    """POST time=HH:MM + date=YYYY-MM-DD → store in session, return summary panel."""

    def post(self, request: HttpRequest) -> HttpResponse:
        time_str = request.POST.get("time", "")
        date_str = request.POST.get("date", "")

        cart = get_cart(request)

        if cart.mode == "multi_day":
            service_id_str = request.POST.get("service_id", "")
            try:
                service_id = int(service_id_str)
                datetime.date.fromisoformat(date_str)
            except ValueError:
                return HttpResponse(status=400)
            cart.set_item_slot(service_id, date_str, time_str)
            save_cart(request, cart)
            logger.debug(
                "Public multi-day slot confirmed: service_id={} date={} time={}",
                service_id,
                date_str,
                time_str,
            )
            return render(
                request,
                "features/booking/partials/scheduler_panel.html",
                {"cart": cart},
            )

        # Same-day mode: Set global date/time and jump to Stage 3 (Information)
        cart.date = date_str
        cart.time = time_str
        cart.stage = 3
        save_cart(request, cart)
        logger.debug("Public same-day slot confirmed: date={} time={} -> Stage 3", date_str, time_str)

        # Immediate transition logic (re-using Stage 3 render)
        content_html = render(request, "features/booking/partials/summary_panel.html", {"cart": cart}).content.decode(
            "utf-8"
        )

        # OOB updates for the layout
        stepper_html = render(request, "features/booking/partials/stepper.html", {"cart": cart}).content.decode("utf-8")
        sidebar_content = render(
            request, "features/booking/partials/summary_sidebar.html", {"cart": cart}
        ).content.decode("utf-8")
        sidebar_html = f'<div id="bk-sidebar-wrapper" hx-swap-oob="innerHTML"><aside class="wizard-sidebar">{sidebar_content}</aside></div>'

        # Prepare response
        response = HttpResponse(content_html + stepper_html + sidebar_html)

        # Trigger stage change (fullWidth = false)
        response["HX-Trigger"] = '{"stageChanged": {"fullWidth": false}}'

        return response
