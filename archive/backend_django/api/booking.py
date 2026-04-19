"""
API endpoints for managing appointments from Telegram Bot.
"""

import re
from datetime import timedelta

from core.logger import log
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from features.booking.models.appointment import Appointment
from features.booking.schemas.appointment_schemas import (
    AppointmentListItem,
    AppointmentListResponse,
    CategorySummaryItem,
    CategorySummaryResponse,
    ExpireRescheduleRequest,
    ExpireRescheduleResponse,
    ManageAppointmentRequest,
    ManageAppointmentResponse,
    ProposeRescheduleRequest,
    ProposeRescheduleResponse,
    SlotItem,
    SlotsResponse,
)
from features.booking.services.slots import SlotService
from features.system.models.site_settings import SiteSettings
from ninja import Router
from ninja.security import APIKeyHeader


class BotApiKey(APIKeyHeader):
    """
    X-API-Key authentication for Telegram Bot.
    Checks for a shared key between Bot and Django (BOT_API_KEY).
    """

    param_name = "X-API-Key"

    def authenticate(self, request, key):
        expected_key = getattr(settings, "BOT_API_KEY", None)
        if expected_key and key == expected_key:
            return key
        return None


router = Router(auth=BotApiKey())


@router.post("/appointments/manage/", response=ManageAppointmentResponse)
def manage_appointment(request, payload: ManageAppointmentRequest):
    """
    Universal endpoint for managing appointments from Telegram Bot.
    Protected by X-API-Key authentication.

    Supported actions:
    - confirm: confirm the appointment
    - cancel: reject the appointment
    """
    log.debug(f"API: Booking | Action: Manage | appt_id={payload.appointment_id} | action={payload.action}")
    appointment = get_object_or_404(Appointment, id=payload.appointment_id)

    from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

    if payload.action == "confirm":
        appointment.status = Appointment.STATUS_CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])

        # Sync cache for the notification worker
        NotificationCacheManager.seed_appointment(appointment.id)

        log.info(f"API: Booking | Action: ConfirmSuccess | appt_id={appointment.id}")
        return ManageAppointmentResponse(success=True, message="Appointment confirmed", appointment_id=appointment.id)

    elif payload.action == "cancel":
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancel_reason = payload.cancel_reason or Appointment.CANCEL_REASON_OTHER
        appointment.cancel_note = payload.cancel_note or ""
        appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

        # Sync cache for the notification worker
        NotificationCacheManager.seed_appointment(appointment.id)

        log.info(f"API: Booking | Action: CancelSuccess | appt_id={appointment.id} | reason={payload.cancel_reason}")
        return ManageAppointmentResponse(success=True, message="Appointment cancelled", appointment_id=appointment.id)

    log.warning(f"API: Booking | Action: Manage | status=UnknownAction | action={payload.action}")
    return ManageAppointmentResponse(
        success=False, message=f"Unknown action: {payload.action}", appointment_id=appointment.id
    )


@router.get("/slots/", response=SlotsResponse)
def get_available_slots(request, appointment_id: int):
    """
    Returns available slots for booking starting from the date of the cancelled appointment.
    Used by Telegram Bot when proposing alternative time to the client.
    Searches for up to 5 slots within a 7-day range starting from the original appointment date.
    """
    log.debug(f"API: Booking | Action: GetSlots | appt_id={appointment_id}")
    appointment = get_object_or_404(Appointment, id=appointment_id)
    slot_service = SlotService()

    site_settings = SiteSettings.load()
    url_path = getattr(site_settings, "url_path_booking", None) or "/booking/"
    site_base_url = getattr(site_settings, "site_base_url", "") or ""
    booking_url = f"{site_base_url.rstrip('/')}{url_path}"

    collected: list[SlotItem] = []
    start_date = timezone.localtime(appointment.datetime_start).date()

    weekday_names = {0: "Mo", 1: "Di", 2: "Mi", 3: "Do", 4: "Fr", 5: "Sa", 6: "So"}

    for delta in range(7):
        if len(collected) >= 5:
            break
        check_date = start_date + timedelta(days=delta)
        slots = slot_service.get_available_slots(
            masters=appointment.master,
            date_obj=check_date,
            duration_minutes=appointment.duration_minutes,
        )
        for time_str in slots:
            if len(collected) >= 5:
                break
            day_name = weekday_names.get(check_date.weekday(), "")
            label = f"{day_name}, {check_date.strftime('%d.%m')} um {time_str}"
            datetime_str = f"{check_date.strftime('%d.%m.%Y')} {time_str}"
            collected.append(SlotItem(label=label, datetime_str=datetime_str))

    log.info(f"API: Booking | Action: GetSlotsSuccess | appt_id={appointment_id} | count={len(collected)}")
    return SlotsResponse(slots=collected, booking_url=booking_url)


@router.post("/appointments/propose/", response=ProposeRescheduleResponse)
def propose_reschedule(request, payload: ProposeRescheduleRequest):
    """
    Cancels the appointment (reason: reschedule) and sends an email to the client
    with a proposal for alternative time and a link to booking.
    Called from Telegram Bot when admin selects a slot to propose.
    """
    log.debug(f"API: Booking | Action: ProposeReschedule | appt_id={payload.appointment_id}")
    appointment = get_object_or_404(Appointment, id=payload.appointment_id)

    from features.cabinet.services.appointment_service import AppointmentService

    if not payload.proposed_slots:
        log.warning(f"API: Booking | Action: ProposeReschedule | status=NoSlots | appt_id={appointment.id}")
        return ProposeRescheduleResponse(
            success=False,
            message="No slots proposed",
            appointment_id=appointment.id,
        )

    slot_label = payload.proposed_slots[0]

    # Try to parse DD.MM and HH:MM
    match = re.search(r"(\d{2}\.\d{2}).*um\s+(\d{2}:\d{2})", slot_label)
    if not match:
        log.error(f"API: Booking | Action: ProposeReschedule | status=InvalidFormat | label={slot_label}")
        return ProposeRescheduleResponse(
            success=False,
            message="Invalid slot format",
            appointment_id=appointment.id,
        )

    date_part, time_part = match.groups()
    current_year = timezone.now().year
    datetime_str = f"{date_part}.{current_year} {time_part}"

    try:
        AppointmentService.propose_reschedule(appointment=appointment, datetime_str=datetime_str, slot_label=slot_label)
        log.info(f"API: Booking | Action: ProposeSuccess | appt_id={appointment.id} | slot={slot_label}")
    except Exception as e:
        log.error(f"API: Booking | Action: ProposeFailed | appt_id={appointment.id} | error={e}")
        return ProposeRescheduleResponse(
            success=False,
            message=str(e),
            appointment_id=appointment.id,
        )

    return ProposeRescheduleResponse(
        success=True,
        message="Appointment cancelled, new slot proposed, task enqueued",
        appointment_id=appointment.id,
    )


@router.post("/appointments/expire/", response=ExpireRescheduleResponse)
def expire_reschedule(request, payload: ExpireRescheduleRequest):
    """
    Cancels an appointment if it is still in RESCHEDULE_PROPOSED
    or PENDING status after 24 hours.
    Called from Telegram Bot (via ARQ command).
    """
    log.debug(f"API: Booking | Action: Expire | appt_id={payload.appointment_id}")
    appointment = get_object_or_404(Appointment, id=payload.appointment_id)

    # If it is not in proposed status, that means it was already interacted with
    if appointment.status not in [Appointment.STATUS_RESCHEDULE_PROPOSED, Appointment.STATUS_PENDING]:
        log.info(f"API: Booking | Action: ExpireIgnore | appt_id={appointment.id} | status={appointment.status}")
        return ExpireRescheduleResponse(
            success=True,
            message="Appointment already confirmed or cancelled",
            appointment_id=appointment.id,
        )

    appointment.status = Appointment.STATUS_CANCELLED
    appointment.cancelled_at = timezone.now()
    appointment.cancel_reason = Appointment.CANCEL_REASON_OTHER
    appointment.cancel_note = "Expired after 24h of no response to proposal."
    appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

    from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

    NotificationCacheManager.seed_appointment(appointment.id)

    log.info(f"API: Booking | Action: ExpireSuccess | appt_id={appointment.id}")
    return ExpireRescheduleResponse(
        success=True,
        message="Unconfirmed appointment cancelled (timeout)",
        appointment_id=appointment.id,
    )


@router.get("/appointments/summary/", response=CategorySummaryResponse)
def get_appointments_summary(request):
    """
    Summary by service categories: total/pending/completed.
    Used by Telegram Bot for dashboard display.
    """
    log.debug("API: Booking | Action: GetSummary")
    from features.main.models.category import Category

    categories = Category.objects.filter(is_active=True).order_by("order", "title")
    result = []
    for cat in categories:
        qs = Appointment.objects.filter(service__category=cat)
        total = qs.count()
        if total == 0:
            continue
        result.append(
            CategorySummaryItem(
                category_slug=cat.slug,
                category_title=cat.title,
                total=total,
                pending=qs.filter(status=Appointment.STATUS_PENDING).count(),
                completed=qs.filter(status=Appointment.STATUS_CONFIRMED).count(),
            )
        )
    log.info(f"API: Booking | Action: GetSummarySuccess | categories_count={len(result)}")
    return CategorySummaryResponse(categories=result)


@router.get("/appointments/list/", response=AppointmentListResponse)
def get_appointments_list(request, category_slug: str, page: int = 1):
    """
    List of appointments by category with pagination (10 per page).
    Used by Telegram Bot to display appointments in a selected category.
    """
    log.debug(f"API: Booking | Action: GetList | category={category_slug} | page={page}")
    page_size = 10
    qs = Appointment.objects.filter(service__category__slug=category_slug).order_by("-datetime_start")
    total = qs.count()
    pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, pages))
    items_qs = qs[(page - 1) * page_size : page * page_size]

    items = [
        AppointmentListItem(
            id=a.id,
            client_name=a.client.display_name() if a.client else "—",
            status=a.status,
            datetime=timezone.localtime(a.datetime_start).strftime("%d.%m.%Y %H:%M"),
        )
        for a in items_qs
    ]
    log.info(f"API: Booking | Action: GetListSuccess | category={category_slug} | total={total}")
    return AppointmentListResponse(items=items, total=total, page=page, pages=pages)
