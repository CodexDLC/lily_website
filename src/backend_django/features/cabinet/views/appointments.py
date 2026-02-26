"""Appointments view: Admin sees all, Client sees own."""

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.generic import TemplateView
from features.cabinet.mixins import CabinetAccessMixin, HtmxCabinetMixin


class AppointmentsView(HtmxCabinetMixin, CabinetAccessMixin, TemplateView):
    template_name = "cabinet/appointments/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Check scope to highlight correct sidebar link
        scope = self.request.GET.get("scope", "")
        ctx["active_section"] = "my_appointments" if scope == "personal" else "appointments"
        from features.booking.models import Appointment

        qs = self._get_queryset(ctx)

        # Filter by status if requested
        status_filter = self.request.GET.get("status", "")
        if status_filter:
            qs = qs.filter(status=status_filter)

        paginator = Paginator(qs, 20)
        page_num = self.request.GET.get("page", 1)
        ctx["page_obj"] = paginator.get_page(page_num)
        ctx["total_count"] = paginator.count
        ctx["status_filter"] = status_filter
        ctx["status_choices"] = Appointment.STATUS_CHOICES
        return ctx

    def _get_queryset(self, ctx):
        from features.booking.models import Appointment

        qs = Appointment.objects.select_related("client", "master", "service").order_by("-datetime_start")

        # Check if we are in "personal" mode (only my appointments)
        scope = self.request.GET.get("scope", "")
        is_personal = scope == "personal" or not self.request.user.is_staff

        if is_personal:
            # Client (or Admin in personal mode) sees only their appointments
            client = ctx.get("cabinet_client")
            qs = qs.filter(client=client) if client else qs.none()

        return qs

    def post(self, request, *args, **kwargs):
        """HTMX inline status update (Admin only) + Notifications."""
        if not request.user.is_staff:
            return JsonResponse({"status": "error", "message": "Forbidden"}, status=403)

        from core.arq.client import DjangoArqClient
        from django.shortcuts import get_object_or_404
        from django.utils import timezone
        from features.booking.models import Appointment
        from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

        appt_id = request.POST.get("id")
        action = request.POST.get("action")  # approve, cancel, get_slots, propose

        appointment = get_object_or_404(Appointment, id=appt_id)

        # 1. GET SLOTS (AJAX helper for reschedule)
        if action == "get_slots":
            from datetime import timedelta

            from features.booking.services.slots import SlotService

            slot_service = SlotService()
            start_date = timezone.localtime(appointment.datetime_start).date()
            weekday_names = {0: "Mo", 1: "Di", 2: "Mi", 3: "Do", 4: "Fr", 5: "Sa", 6: "So"}

            collected: list[dict[str, str]] = []
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
                    collected.append({"label": label, "datetime_str": datetime_str})

            return JsonResponse({"status": "ok", "slots": collected})

        # ... (previous code for actions: approve, cancel, propose) ...
        # (Note: For all actions that modify status, we now return the template)

        # 2. APPROVE
        if action == "approve":
            appointment.status = Appointment.STATUS_CONFIRMED
            appointment.save(update_fields=["status", "updated_at"])
            NotificationCacheManager.seed_appointment(appointment.id)
            DjangoArqClient.enqueue_job(
                "send_appointment_notification", appointment_id=appointment.id, status="confirmed"
            )

        # 3. REJECT (Cancel)
        elif action == "cancel":
            reason_code = request.POST.get("reason_code")
            reason_text = request.POST.get("reason_text", "")
            appointment.status = Appointment.STATUS_CANCELLED
            appointment.cancelled_at = timezone.now()
            appointment.cancel_reason = reason_code or Appointment.CANCEL_REASON_OTHER
            appointment.cancel_note = reason_text
            appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])
            NotificationCacheManager.seed_appointment(appointment.id)
            DjangoArqClient.enqueue_job(
                "send_appointment_notification",
                appointment_id=appointment.id,
                status="cancelled",
                reason_text=reason_text,
            )

        # 4. PROPOSE (Reschedule)
        elif action == "propose":
            slot_label = request.POST.get("slot_label")
            appointment.status = Appointment.STATUS_CANCELLED
            appointment.cancelled_at = timezone.now()
            appointment.cancel_reason = Appointment.CANCEL_REASON_RESCHEDULE
            appointment.cancel_note = f"Предложено время: {slot_label}"
            appointment.save(update_fields=["status", "cancelled_at", "cancel_reason", "cancel_note", "updated_at"])
            NotificationCacheManager.seed_appointment(appointment.id)
            # Enqueue email... (omitted detailed logic here for brevity in Replace, but I'll make sure it's in final)
            self._send_reschedule_email(appointment, slot_label)

        # 5. EDIT/SAVE
        else:
            new_status = request.POST.get("status")
            if new_status:
                appointment.status = new_status
                appointment.admin_notes = request.POST.get("admin_notes", "")
                appointment.save()

        # RETURN HTMX PARTIAL OR JSON
        if request.headers.get("HX-Request"):
            from django.shortcuts import render

            ctx = self.get_context_data()
            ctx["appt"] = appointment
            return render(request, "cabinet/appointments/includes/_appointment_card.html", ctx)

        return JsonResponse({"status": "ok"})

    def _send_reschedule_email(self, appointment, slot_label):
        import json

        from core.arq.client import DjangoArqClient
        from features.system.models.site_settings import SiteSettings
        from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

        redis_client = NotificationCacheManager.get_redis_client()
        raw = redis_client.get(f"{NotificationCacheManager.APPOINTMENT_CACHE_PREFIX}{appointment.id}")
        cache_data = json.loads(raw) if raw else {}
        client_email = cache_data.get("client_email")

        if client_email and client_email != "не указан":
            site_settings = SiteSettings.load()
            booking_url = f"{site_settings.site_base_url.rstrip('/')}{site_settings.url_path_booking or '/booking/'}"
            email_data = {**cache_data, "proposed_slots": [slot_label], "link_reschedule": booking_url}
            DjangoArqClient.enqueue_job(
                "send_email_task",
                recipient_email=client_email,
                subject="Terminvorschlag - Lily Beauty Salon",
                template_name="reschedule_offer.html",
                data=email_data,
            )
