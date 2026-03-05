from datetime import datetime, timedelta

from core.arq.client import DjangoArqClient
from django.utils import timezone
from features.booking.models import Appointment
from features.booking.services.reschedule import RescheduleTokenService
from features.booking.services.slots import SlotService
from features.system.models.site_settings import SiteSettings
from features.system.services.notification import NotificationService
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
        """Approves a pending appointment and sends confirmation."""
        appointment.status = Appointment.STATUS_CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])

        if appointment.client.email:
            NotificationService.send_booking_confirmation(
                recipient_email=appointment.client.email,
                client_name=appointment.client.first_name,
                context=AppointmentService._build_email_context(appointment),
            )
        log.info(f"Appointment #{appointment.id} approved and confirmation sent.")

    @staticmethod
    def cancel_appointment(appointment: Appointment, reason_code: str, reason_text: str) -> None:
        """Cancels an appointment and sends notification."""
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancel_reason = reason_code or Appointment.CANCEL_REASON_OTHER
        appointment.cancel_note = reason_text
        appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

        if appointment.client.email:
            ctx = AppointmentService._build_email_context(appointment)
            ctx["reason_text"] = reason_text

            NotificationService.send_booking_cancellation(
                recipient_email=appointment.client.email, client_name=appointment.client.first_name, context=ctx
            )
        log.info(f"Appointment #{appointment.id} cancelled. Reason: {reason_code}")

    @staticmethod
    def update_appointment(appointment: Appointment, new_status: str, admin_notes: str | None = None) -> None:
        """Update appointment status and admin notes directly."""
        old_status = appointment.status

        if new_status:
            appointment.status = new_status
        if admin_notes is not None:
            appointment.admin_notes = admin_notes
        appointment.save()

        # If completed -> send "Thank you / Review" email
        if (
            new_status == Appointment.STATUS_COMPLETED
            and old_status != Appointment.STATUS_COMPLETED
            and appointment.client.email
        ):
            NotificationService.send_universal(
                recipient_email=appointment.client.email,
                first_name=appointment.client.first_name,
                template_name="mk_reengagement",
                subject="Vielen Dank für Ihren Besuch!",
                context_data=AppointmentService._build_email_context(appointment),
                channels=["email"],
            )

        # If No Show -> send "Missed Appointment" email
        if (
            new_status == Appointment.STATUS_NO_SHOW
            and old_status != Appointment.STATUS_NO_SHOW
            and appointment.client.email
        ):
            NotificationService.send_booking_no_show(
                recipient_email=appointment.client.email,
                client_name=appointment.client.first_name,
                context=AppointmentService._build_email_context(appointment),
            )

    @staticmethod
    def reschedule_appointment(appointment: Appointment, new_start: datetime) -> None:
        """Update appointment start time directly."""
        appointment.datetime_start = new_start
        appointment.save(update_fields=["datetime_start", "updated_at"])
        log.info(f"Appointment #{appointment.id} rescheduled to {new_start}.")

    @staticmethod
    def propose_reschedule(appointment: Appointment, datetime_str: str, slot_label: str) -> None:
        """Proposes a reschedule to the client for a new date and time."""

        log.debug(f"Proposing reschedule for appointment #{appointment.id} to new slot: {slot_label} ({datetime_str})")

        # 1. Cancel old
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancel_reason = Appointment.CANCEL_REASON_RESCHEDULE
        appointment.cancel_note = f"Reschedule proposed: {slot_label}"
        appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])

        # 2. Create new
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

        # 3. Generate token
        token = RescheduleTokenService.create_token(appointment_id=new_appointment.id, proposed_slot=slot_label)

        # 4. Enqueue expiration
        try:
            DjangoArqClient.enqueue_job(
                "expire_reservation_task", appointment_id=new_appointment.id, _defer_by=timedelta(hours=24)
            )
        except Exception as e:
            log.error(f"Failed to enqueue expire task: {e}")

        # 5. Send Email via Universal Gateway
        if appointment.client.email:
            site_settings = SiteSettings.load()
            base_url = site_settings.site_base_url.rstrip("/")
            reschedule_url = f"{base_url}/de/cabinet/appointments/reschedule/{token}/"

            ctx = AppointmentService._build_email_context(new_appointment)
            ctx["link_reschedule"] = reschedule_url
            ctx["is_reschedule_offer"] = True

            NotificationService.send_universal(
                recipient_email=appointment.client.email,
                first_name=appointment.client.first_name,
                template_name="bk_reschedule",
                subject="Terminvorschlag - Lily Beauty Salon",
                context_data=ctx,
                channels=["email"],
            )

    @staticmethod
    def _build_email_context(appointment: Appointment) -> dict:
        """Helper to build standard context for booking emails."""
        local_dt = timezone.localtime(appointment.datetime_start)
        return {
            "appointment_id": appointment.id,
            "service_name": appointment.service.title,
            "master_name": appointment.master.name,
            "date": local_dt.strftime("%d.%m.%Y"),
            "time": local_dt.strftime("%H:%M"),
            "price": str(appointment.price),
            "duration_minutes": appointment.duration_minutes,
            "datetime": local_dt.strftime("%d.%m.%Y %H:%M"),  # For calendar generation
        }
