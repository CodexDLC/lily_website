import json
from datetime import timedelta

from core.arq.client import DjangoArqClient
from django.utils import timezone
from features.booking.models import Appointment
from features.booking.services.reschedule import RescheduleTokenService
from features.booking.services.slots import SlotService
from features.system.models.site_settings import SiteSettings
from features.system.redis_managers.notification_cache_manager import NotificationCacheManager
from loguru import logger as log


class AppointmentService:
    """Service layer for business logic involving appointments in the cabinet."""

    @staticmethod
    def get_upcoming_slots(
        appointment: Appointment, days_to_check: int = 7, max_slots: int = 5
    ) -> list[dict[str, str]]:
        """Returns the next available generic slots for rescheduling."""
        slot_service = SlotService()
        start_date = timezone.localtime(appointment.datetime_start).date()
        weekday_names = {0: "Mo", 1: "Di", 2: "Mi", 3: "Do", 4: "Fr", 5: "Sa", 6: "So"}

        collected: list[dict[str, str]] = []
        for delta in range(days_to_check):
            if len(collected) >= max_slots:
                break
            check_date = start_date + timedelta(days=delta)
            slots = slot_service.get_available_slots(
                masters=appointment.master,
                date_obj=check_date,
                duration_minutes=appointment.duration_minutes,
            )
            for time_str in slots:
                if len(collected) >= max_slots:
                    break
                day_name = weekday_names.get(check_date.weekday(), "")
                label = f"{day_name}, {check_date.strftime('%d.%m')} um {time_str}"
                datetime_str = f"{check_date.strftime('%d.%m.%Y')} {time_str}"
                collected.append({"label": label, "datetime_str": datetime_str})

        return collected

    @staticmethod
    def approve_appointment(appointment: Appointment) -> None:
        """Approves a pending appointment."""
        appointment.status = Appointment.STATUS_CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])
        NotificationCacheManager.seed_appointment(appointment.id)
        DjangoArqClient.enqueue_job("send_appointment_notification", appointment_id=appointment.id, status="confirmed")

    @staticmethod
    def cancel_appointment(appointment: Appointment, reason_code: str, reason_text: str) -> None:
        """Cancels an appointment with a given reason."""
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancel_reason = reason_code or Appointment.CANCEL_REASON_OTHER
        appointment.cancel_note = reason_text
        appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])
        NotificationCacheManager.seed_appointment(appointment.id)

        # Enqueue the cancellation email separately, specifying the reason text to be included
        DjangoArqClient.enqueue_job(
            "send_appointment_notification",
            appointment_id=appointment.id,
            status="cancelled",
            reason_text=reason_text,
        )

    @staticmethod
    def propose_reschedule(appointment: Appointment, datetime_str: str, slot_label: str) -> None:
        """Proposes a reschedule to the client for a new date and time."""
        from datetime import datetime

        log.debug(f"Proposing reschedule for appointment #{appointment.id} to new slot: {slot_label} ({datetime_str})")
        # 1. Cancel the old appointment marking it as rescheduled
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancel_reason = Appointment.CANCEL_REASON_RESCHEDULE
        appointment.cancel_note = f"Reschedule proposed: {slot_label}"
        appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])
        NotificationCacheManager.seed_appointment(appointment.id)
        log.info(f"Old appointment #{appointment.id} cancelled with status 'reschedule'")

        # 2. Create the proposed appointment
        new_start = timezone.make_aware(datetime.strptime(datetime_str, "%d.%m.%Y %H:%M"))
        new_appointment = Appointment.objects.create(
            client=appointment.client,
            master=appointment.master,
            service=appointment.service,
            datetime_start=new_start,
            duration_minutes=appointment.duration_minutes,
            price=appointment.price,
            status=Appointment.STATUS_RESCHEDULE_PROPOSED,
            source=appointment.source,
            client_notes=appointment.client_notes,
            admin_notes="Pending client confirmation (proposed by admin)",
        )
        log.info(f"Created new proposed appointment #{new_appointment.id} for client {appointment.client.phone}")

        # 3. Generate 24hr token
        token = RescheduleTokenService.create_token(appointment_id=new_appointment.id, proposed_slot=slot_label)

        # 4. Enqueue expiration task
        try:
            DjangoArqClient.enqueue_job(
                "expire_reservation_task", appointment_id=new_appointment.id, _defer_by=timedelta(hours=24)
            )
            log.info(f"Enqueued expire_reservation_task for proposed appointment #{new_appointment.id}")
        except Exception as e:
            log.error(f"Failed to enqueue expire task: {e}")

        # 5. Send Email
        AppointmentService._send_reschedule_email(appointment, new_appointment, slot_label, token)

    @staticmethod
    def _send_reschedule_email(
        old_appointment: Appointment, new_appointment: Appointment, slot_label: str, token: str
    ) -> None:
        """Sends the reschedule offer email."""
        redis_client = NotificationCacheManager.get_redis_client()
        raw = redis_client.get(f"{NotificationCacheManager.APPOINTMENT_CACHE_PREFIX}{old_appointment.id}")
        cache_data = json.loads(raw) if raw else {}
        client_email = cache_data.get("client_email")

        if client_email and client_email != "n/a":
            site_settings = SiteSettings.load()
            settings_dict = site_settings.to_dict()
            base_url = settings_dict.get("site_base_url", "").rstrip("/")

            # The URL route is defined in cabinet/urls.py as 'appointments/reschedule/<str:token>/'
            # We add /de/ prefix because it's under i18n_patterns
            reschedule_url = f"{base_url}/de/cabinet/appointments/reschedule/{token}/"
            log.debug(f"Generated reschedule URL: {reschedule_url}")

            # The email template uses `date` and `time`
            # We must override the old cache values with the NEW appointment's date/time
            local_dt = timezone.localtime(new_appointment.datetime_start)
            new_date = local_dt.strftime("%d.%m.%Y")
            new_time = local_dt.strftime("%H:%M")

            email_data = {
                **cache_data,
                "date": new_date,
                "time": new_time,
                "proposed_slots": [slot_label],
                "link_reschedule": reschedule_url,
                "timeout_hours": 24,
                "is_reschedule_offer": True,
            }
            DjangoArqClient.enqueue_job(
                "send_email_task",
                recipient_email=client_email,
                subject="Terminvorschlag - Lily Beauty Salon",
                template_name="reschedule_offer.html",
                data=email_data,
            )
            log.info(
                f"Enqueued email task to {client_email} for reschedule of #{old_appointment.id} -> #{new_appointment.id}"
            )
        else:
            log.warning(f"Skipping email for appointment #{old_appointment.id}: No valid client email found in cache")

    @staticmethod
    def update_appointment(appointment: Appointment, new_status: str, admin_notes: str) -> None:
        """Update appointment status and admin notes directly."""
        if new_status:
            appointment.status = new_status
        if admin_notes is not None:
            appointment.admin_notes = admin_notes
        appointment.save()
