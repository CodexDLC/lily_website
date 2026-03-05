"""Reschedule Appointment View."""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import TemplateView
from features.booking.models.appointment import Appointment
from features.booking.services.reschedule import RescheduleTokenService
from features.booking.services.slots import SlotService
from features.system.redis_managers.notification_cache_manager import NotificationCacheManager
from loguru import logger


class RescheduleAppointmentView(TemplateView):
    """
    Handles the client-side of the rescheduling flow via token.
    Uses HTMX for partial updates.
    """

    template_name = "cabinet/crm/appointments/reschedule.html"

    def dispatch(self, request, *args, **kwargs):
        self.token = kwargs.get("token")
        self.token_data = RescheduleTokenService.get_token_data(self.token)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["token"] = self.token
        ctx["valid_token"] = bool(self.token_data)

        if self.token_data:
            appointment_id = self.token_data["appointment_id"]
            appointment = get_object_or_404(Appointment, id=appointment_id)
            ctx["appointment"] = appointment
            ctx["proposed_slot"] = self.token_data["proposed_slot"]

            # If the appointment was already acted upon, it shouldn't be valid anymore
            if appointment.status != Appointment.STATUS_RESCHEDULE_PROPOSED:
                ctx["valid_token"] = False
                ctx["error_message"] = "Данное предложение уже обработано или истекло."

        return ctx

    def post(self, request, *args, **kwargs):
        """Handle confirmations and slot selections (HTMX)."""
        logger.info("RescheduleAppointmentView.post: token={}", self.token)

        if not self.token_data:
            logger.error("RescheduleAppointmentView.post: Invalid or expired token.")
            return HttpResponse('<div class="alert alert-danger">Токен недействителен или истек.</div>')

        appointment_id = self.token_data["appointment_id"]
        appointment = get_object_or_404(Appointment, id=appointment_id)

        logger.info("RescheduleAppointmentView.post: appointment_id={}, status={}", appointment_id, appointment.status)

        if appointment.status != Appointment.STATUS_RESCHEDULE_PROPOSED:
            logger.error(
                "RescheduleAppointmentView.post: Appointment status is {}, expected {}",
                appointment.status,
                Appointment.STATUS_RESCHEDULE_PROPOSED,
            )
            return HttpResponse('<div class="alert alert-danger">Предложение больше не актуально.</div>')

        action = request.POST.get("action")
        logger.info("RescheduleAppointmentView.post: action={}", action)

        # 1. User confirms the PROPOSED time
        if action == "confirm":
            logger.info("Confirming proposed slot for appointment {}", appointment_id)
            appointment.status = Appointment.STATUS_CONFIRMED
            appointment.save(update_fields=["status", "updated_at"])
            NotificationCacheManager.seed_appointment(appointment.id)
            RescheduleTokenService.delete_token(self.token)

            from core.arq.client import DjangoArqClient

            # Notify client and master about confirmation
            DjangoArqClient.enqueue_job(
                "send_appointment_notification", appointment_id=appointment.id, status="confirmed"
            )
            logger.success("Appointment {} confirmed successfully (proposed time).", appointment_id)

            return render(
                request, "cabinet/crm/appointments/includes/_reschedule_success.html", {"appointment": appointment}
            )

        # 2. User confirms a NEW picked time
        elif action == "confirm_new_slot":
            datetime_str = request.POST.get("datetime_str")
            logger.info("Confirming NEW slot {} for appointment {}", datetime_str, appointment_id)
            from datetime import datetime

            try:
                new_start = timezone.make_aware(datetime.strptime(datetime_str, "%d.%m.%Y %H:%M"))
                appointment.datetime_start = new_start
                appointment.status = Appointment.STATUS_CONFIRMED
                appointment.admin_notes = appointment.admin_notes + "\n(Время изменено клиентом при переносе)"
                appointment.save(update_fields=["datetime_start", "status", "admin_notes", "updated_at"])

                NotificationCacheManager.seed_appointment(appointment.id)
                RescheduleTokenService.delete_token(self.token)

                from core.arq.client import DjangoArqClient

                # Notify client and master about confirmation
                DjangoArqClient.enqueue_job(
                    "send_appointment_notification", appointment_id=appointment.id, status="confirmed"
                )
                logger.success("Appointment {} confirmed successfully with NEW time {}.", appointment_id, datetime_str)

                return render(
                    request, "cabinet/crm/appointments/includes/_reschedule_success.html", {"appointment": appointment}
                )
            except ValueError as e:
                logger.error("ValueError parsing datetime {}: {}", datetime_str, e)
                return HttpResponse('<div class="alert alert-danger">Неверный формат времени.</div>')

        logger.warning("Unknown action received: {}", action)
        return HttpResponse('<div class="alert alert-danger">Неизвестное действие.</div>')

    def _get_calendar_grid(self, year: int, month: int):
        """Helper to generate calendar matrix for grid view."""
        import calendar
        from datetime import date

        from holidays.countries import Germany

        de_holidays = Germany(subdiv="ST", years=year)
        cal = calendar.Calendar(firstweekday=0)
        matrix = cal.monthdayscalendar(year, month)

        days_list = []
        today = timezone.localtime(timezone.now()).date()

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

                days_list.append(
                    {"num": str(day_num), "status": status, "title": title, "date": current_date.isoformat()}
                )

        # German month names for consistency
        from django.utils.translation import gettext as _

        month_label = _(date(year, month, 1).strftime("%B")) + f" {year}"

        return {"calendar_days": days_list, "month_label": month_label, "current_year": year, "current_month": month}

    def get(self, request, *args, **kwargs):
        """Handle HTMX GET requests for calendar and slots."""

        # Primary page load
        if not request.headers.get("HX-Request"):
            return super().get(request, *args, **kwargs)

        if not self.token_data:
            return HttpResponse('<div class="alert alert-danger">Токен недействителен или истек.</div>')

        appointment_id = self.token_data["appointment_id"]
        appointment = get_object_or_404(Appointment, id=appointment_id)
        action = request.GET.get("action")

        # 1. Load Calendar grid
        if action == "load_calendar":
            today = timezone.localtime(timezone.now()).date()
            try:
                year = int(request.GET.get("year", today.year))
                month = int(request.GET.get("month", today.month))
                # Basic wrap around for months
                if month > 12:
                    month = 1
                    year += 1
                elif month < 1:
                    month = 12
                    year -= 1
            except (ValueError, TypeError):
                year, month = today.year, today.month

            calendar_data = self._get_calendar_grid(year, month)
            ctx = {"token": self.token, "appointment": appointment, **calendar_data}
            return render(request, "cabinet/crm/appointments/includes/_reschedule_calendar.html", ctx)

        # 2. Load Slots for a date
        elif action == "load_slots":
            date_str = request.GET.get("date")
            from datetime import datetime

            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                slot_service = SlotService()
                slots = slot_service.get_available_slots(
                    masters=appointment.master,
                    date_obj=date_obj,
                    duration_minutes=appointment.duration_minutes,
                )

                slots_data = []
                for time_str in slots:
                    # Creating a display-friendly label and a data string for the form
                    full_datetime_str = f"{date_obj.strftime('%d.%m.%Y')} {time_str}"
                    slots_data.append({"time": time_str, "datetime_str": full_datetime_str})

                return render(
                    request,
                    "cabinet/crm/appointments/includes/_reschedule_slots.html",
                    {"slots": slots_data, "token": self.token, "selected_date": date_obj},
                )
            except ValueError:
                return HttpResponse('<div class="alert alert-danger">Неверная дата.</div>')

        return HttpResponse('<div class="alert alert-warning">Unknown action.</div>')
