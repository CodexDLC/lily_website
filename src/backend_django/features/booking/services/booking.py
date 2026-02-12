from datetime import datetime
from typing import Any, cast

from core.logger import log
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

        # 3. Handle Client
        client = ClientService.get_or_create_client(
            first_name=form_data.get("first_name", ""),
            last_name=form_data.get("last_name", ""),
            phone=form_data.get("phone", ""),
            email=form_data.get("email", ""),
            consent_marketing=True,
        )

        # 4. Create Appointment
        appointment = BookingService._create_appointment_record(client, master, service, start_dt)

        # 5. Post-processing
        BookingService._handle_post_creation(appointment, form_data)

        return appointment

    @staticmethod
    def _validate_and_parse(state: BookingState) -> datetime | None:
        """Validates state and parses datetime."""
        if not all([state.service_id, state.master_id, state.selected_date, state.selected_time]):
            log.error("Missing state data for booking")
            return None

        try:
            start_dt = datetime.strptime(f"{state.selected_date.isoformat()} {state.selected_time}", "%Y-%m-%d %H:%M")
            return cast("datetime", timezone.make_aware(start_dt))
        except ValueError:
            log.error("Invalid date/time format in state")
            return None

    @staticmethod
    def _get_objects(service_id: int, master_id: str) -> tuple[Service, Master] | None:
        """Fetches Service and Master objects."""
        try:
            service = Service.objects.get(id=service_id)
            # master_id can be 'any', but for booking it must be a specific master.
            # This logic should be handled before calling create_appointment.
            # Let's assume at this stage master_id is a valid integer ID.
            master = Master.objects.get(id=int(master_id))
            return service, master
        except (Service.DoesNotExist, Master.DoesNotExist, ValueError, TypeError):
            log.error(f"Service or Master not found for service_id={service_id}, master_id={master_id}")
            return None

    @staticmethod
    def _create_appointment_record(client: Client, master: Master, service: Service, start_dt: datetime) -> Appointment:
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
        )
        log.info(f"Appointment created: {appointment.id} for {client}")
        return appointment

    @staticmethod
    def _handle_post_creation(appointment: Appointment, form_data: dict[str, Any]) -> None:
        """Handles notifications and extra flags."""
        from core.arq.client import DjangoArqClient
        from django.conf import settings

        # 1. Подготовить данные для задачи
        appointment_data = {
            "id": appointment.id,
            "client_name": f"{appointment.client.first_name} {appointment.client.last_name}",
            "client_phone": appointment.client.phone or "не указан",
            "client_email": appointment.client.email or "не указан",
            "service_name": appointment.service.title,  # Service использует 'title', не 'name'
            "master_name": appointment.master.name,
            "datetime": appointment.datetime_start.strftime("%d.%m.%Y %H:%M"),
            "price": float(appointment.price),
            "request_call": form_data.get("request_call", False),
        }

        # 2. Отправить задачу в Bot Worker
        if settings.TELEGRAM_ADMIN_ID:
            try:
                DjangoArqClient.enqueue_job(
                    "send_booking_notification_task",
                    admin_id=int(settings.TELEGRAM_ADMIN_ID),
                    appointment_data=appointment_data,
                )
                log.info(f"Queued booking notification for appointment {appointment.id}")
            except Exception as e:
                # Не прерываем создание записи, если очередь не работает
                log.error(f"Failed to queue notification: {e}")
        else:
            log.warning("TELEGRAM_ADMIN_ID not configured, skipping notification")
