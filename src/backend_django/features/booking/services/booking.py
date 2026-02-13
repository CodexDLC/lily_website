from datetime import datetime, timedelta
from typing import Any, cast

from core.logger import log
from django.db import transaction
from django.utils import timezone
from features.booking.dto import BookingState
from features.booking.models.appointment import Appointment
from features.booking.models.client import Client
from features.booking.models.master import Master
from features.booking.services.client_service import ClientService
from features.main.models.service import Service


class BookingService:
    """
    Service for creating appointments.
    Stateless, use static methods.
    """

    @staticmethod
    def create_appointment(state: BookingState, form_data: dict[str, Any]) -> Appointment | None:
        """
        Main entry point. Orchestrates validation, object fetching, and creation.
        Uses atomic transaction to prevent double-booking.
        """
        # 1. Validate & Parse
        validated_data = BookingService._validate_and_parse(state)
        if not validated_data:
            return None

        start_dt = validated_data

        # 2. Get Objects
        objects = BookingService._get_objects(state.service_id, state.master_id)
        if not objects:
            return None

        service, master = objects

        # 3. Final Availability Check (Double-booking protection)
        with transaction.atomic():
            if not BookingService._is_slot_still_available(master, start_dt, service.duration):
                log.warning(f"Double-booking prevented for master {master} at {start_dt}")
                return None

            # 4. Handle Client
            client = ClientService.get_or_create_client(
                first_name=form_data.get("first_name", ""),
                last_name=form_data.get("last_name", ""),
                phone=form_data.get("phone", ""),
                email=form_data.get("email", ""),
                consent_marketing=True,
            )

            # 5. Create Appointment
            appointment = BookingService._create_appointment_record(client, master, service, start_dt, form_data)

        # 6. Post-processing (Notifications) - Outside transaction
        BookingService._handle_post_creation(appointment, form_data)

        return appointment

    @staticmethod
    def _is_slot_still_available(master: Master, start_dt: datetime, duration_minutes: int) -> bool:
        """
        Checks if the master is still free for the given time interval.
        """
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Since we can't easily calculate end_time in a simple SQL filter without extra fields,
        # we'll fetch today's appointments and check in Python (safe within transaction)
        today_appointments = Appointment.objects.filter(
            master=master,
            datetime_start__date=start_dt.date(),
            status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED],
        ).select_for_update()  # Lock rows for this master

        for app in today_appointments:
            app_start = app.datetime_start
            app_end = app_start + timedelta(minutes=app.duration_minutes)

            if start_dt < app_end and end_dt > app_start:
                return False  # Collision found

        return True

    @staticmethod
    def _validate_and_parse(state: BookingState) -> datetime | None:
        """Validates state and parses datetime."""
        if not all([state.service_id, state.master_id, state.selected_date, state.selected_time]):
            log.error("Missing state data for booking")
            return None

        try:
            # Combine date and time string
            date_str = (
                state.selected_date.isoformat()
                if hasattr(state.selected_date, "isoformat")
                else str(state.selected_date)
            )
            start_dt = datetime.strptime(f"{date_str} {state.selected_time}", "%Y-%m-%d %H:%M")
            return cast("datetime", timezone.make_aware(start_dt))
        except ValueError:
            log.error("Invalid date/time format in state")
            return None

    @staticmethod
    def _get_objects(service_id: int, master_id: str) -> tuple[Service, Master] | None:
        """Fetches Service and Master objects."""
        try:
            service = Service.objects.get(id=service_id)
            master = Master.objects.get(id=int(master_id))
            return service, master
        except (Service.DoesNotExist, Master.DoesNotExist, ValueError, TypeError):
            log.error(f"Service or Master not found for service_id={service_id}, master_id={master_id}")
            return None

    @staticmethod
    def _create_appointment_record(
        client: Client, master: Master, service: Service, start_dt: datetime, form_data: dict[str, Any]
    ) -> Appointment:
        """Creates the Appointment database record."""
        appointment = Appointment.objects.create(
            client=client,
            master=master,
            service=service,
            datetime_start=start_dt,
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_PENDING,
            source="website",
            client_notes=form_data.get("client_notes", ""),
        )
        log.info(f"Appointment created: {appointment.id} for {client}")
        return appointment

    @staticmethod
    def _handle_post_creation(appointment: Appointment, form_data: dict[str, Any]) -> None:
        """Handles notifications and extra flags."""
        from core.arq.client import DjangoArqClient
        from django.conf import settings

        visits_count = Appointment.objects.filter(
            client=appointment.client, status=Appointment.STATUS_COMPLETED
        ).count()

        appointment_data = {
            "id": appointment.id,
            "client_name": f"{appointment.client.first_name} {appointment.client.last_name}",
            "client_phone": appointment.client.phone or "не указан",
            "client_email": appointment.client.email or "не указан",
            "service_name": appointment.service.title,
            "master_name": appointment.master.name,
            "datetime": appointment.datetime_start.strftime("%d.%m.%Y %H:%M"),
            "price": float(appointment.price),
            "request_call": form_data.get("request_call", False),
            "client_notes": appointment.client_notes,
            "visits_count": visits_count,
            "category_slug": appointment.service.category.slug if appointment.service.category else None,
        }

        if settings.TELEGRAM_ADMIN_ID:
            try:
                DjangoArqClient.enqueue_job(
                    "send_booking_notification_task",
                    admin_id=int(settings.TELEGRAM_ADMIN_ID),
                    appointment_data=appointment_data,
                )
                log.info(f"Queued booking notification for appointment {appointment.id}")
            except Exception as e:
                log.error(f"Failed to queue notification: {e}")
