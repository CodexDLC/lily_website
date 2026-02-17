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

        # 2. Get Objects (Handle "any" master logic)
        objects = BookingService._get_objects(state.service_id, state.master_id)
        if not objects:
            return None

        service, master = objects

        # 3. Final Availability Check
        # If master was "any", we might need to find a free one here if _get_objects didn't check availability
        # But let's assume _get_objects returns a candidate, and we verify it here.

        with transaction.atomic():
            # If master_id was "any", we need to be sure this specific master is free.
            # If not, we could try another one, but for simplicity, let's just fail or rely on _get_objects logic.

            # If master_id was "any", _get_objects returned *some* master.
            # We must check if they are free.
            if not BookingService._is_slot_still_available(master, start_dt, service.duration):
                # If the chosen "any" master is busy, try to find another one?
                if state.master_id == "any":
                    log.info(f"Master {master} is busy, trying to find another for 'any' selection...")
                    alternative_master = BookingService._find_free_master(service, start_dt)
                    if alternative_master:
                        master = alternative_master
                        log.info(f"Found alternative master: {master}")
                    else:
                        log.warning(f"No alternative masters found at {start_dt}")
                        return None
                else:
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

        # 6. Post-processing (Notifications)
        BookingService._handle_post_creation(appointment, form_data)

        return appointment

    @staticmethod
    def _is_slot_still_available(master: Master, start_dt: datetime, duration_minutes: int) -> bool:
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        today_appointments = Appointment.objects.filter(
            master=master,
            datetime_start__date=start_dt.date(),
            status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED],
        ).select_for_update()

        for app in today_appointments:
            app_start = app.datetime_start
            app_end = app_start + timedelta(minutes=app.duration_minutes)
            if start_dt < app_end and end_dt > app_start:
                return False
        return True

    @staticmethod
    def _find_free_master(service: Service, start_dt: datetime) -> Master | None:
        """Finds any active master who can perform the service and is free at start_dt."""
        candidates = Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE)

        for master in candidates:
            if BookingService._is_slot_still_available(master, start_dt, service.duration):
                return master
        return None

    @staticmethod
    def _validate_and_parse(state: BookingState) -> datetime | None:
        if not all([state.service_id, state.master_id, state.selected_date, state.selected_time]):
            return None
        try:
            date_str = (
                state.selected_date.isoformat()
                if hasattr(state.selected_date, "isoformat")
                else str(state.selected_date)
            )
            start_dt = datetime.strptime(f"{date_str} {state.selected_time}", "%Y-%m-%d %H:%M")
            return cast("datetime", timezone.make_aware(start_dt))
        except ValueError:
            return None

    @staticmethod
    def _get_objects(service_id: int, master_id: str) -> tuple[Service, Master] | None:
        try:
            service = Service.objects.get(id=service_id)

            if master_id == "any":
                # Return the first candidate to start with.
                # Real availability check happens in create_appointment loop.
                master = Master.objects.filter(categories=service.category, status=Master.STATUS_ACTIVE).first()

                if not master:
                    return None
            else:
                master = Master.objects.get(id=int(master_id))

            return service, master
        except (Service.DoesNotExist, Master.DoesNotExist, ValueError, TypeError):
            return None

    @staticmethod
    def _create_appointment_record(
        client: Client, master: Master, service: Service, start_dt: datetime, form_data: dict[str, Any]
    ) -> Appointment:
        # Get active promo at booking time (only for website bookings)
        active_promo = None
        if service.category:
            try:
                from features.promos.services import PromoService

                active_promo = PromoService.get_active_promo(service.category.slug)
            except Exception as e:
                log.warning(f"Failed to get active promo: {e}")

        return Appointment.objects.create(
            client=client,
            master=master,
            service=service,
            datetime_start=start_dt,
            duration_minutes=service.duration,
            price=service.price,
            status=Appointment.STATUS_PENDING,
            source="website",
            client_notes=form_data.get("client_notes", ""),
            active_promo=active_promo,
        )

    @staticmethod
    def _handle_post_creation(appointment: Appointment, form_data: dict[str, Any]) -> None:
        from core.arq.client import DjangoArqClient

        visits_count = Appointment.objects.filter(
            client=appointment.client, status=Appointment.STATUS_COMPLETED
        ).count()

        appointment_data = {
            "id": appointment.id,
            "client_name": f"{appointment.client.first_name} {appointment.client.last_name}",
            "first_name": appointment.client.first_name,
            "last_name": appointment.client.last_name,
            "client_phone": appointment.client.phone or "не указан",
            "client_email": appointment.client.email or "не указан",
            "service_name": appointment.service.title,
            "master_name": appointment.master.name,
            "datetime": appointment.datetime_start.strftime("%d.%m.%Y %H:%M"),
            "duration_minutes": appointment.duration_minutes,  # <--- ДОБАВИЛИ
            "price": float(appointment.price),
            "request_call": form_data.get("request_call", False),
            "client_notes": appointment.client_notes,
            "visits_count": visits_count,
            "category_slug": appointment.service.category.slug if appointment.service.category else None,
            "active_promo_id": appointment.active_promo.id if appointment.active_promo else None,
            "active_promo_title": appointment.active_promo.title if appointment.active_promo else None,
        }

        try:
            DjangoArqClient.enqueue_job(
                "send_booking_notification_task",
                appointment_data=appointment_data,
            )
        except Exception as e:
            log.error(f"Failed to queue notification: {e}")
