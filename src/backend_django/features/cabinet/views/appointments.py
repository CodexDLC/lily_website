"""Appointments view: Admin sees all, Client sees own."""

from core.logger import log
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView
from features.cabinet.mixins import CabinetAccessMixin, HtmxCabinetMixin


class AppointmentsView(HtmxCabinetMixin, CabinetAccessMixin, TemplateView):
    template_name = "cabinet/appointments/list.html"

    def get_context_data(self, **kwargs):
        log.debug(f"View: AppointmentsView | Action: GetContext | user={self.request.user.id}")
        ctx = super().get_context_data(**kwargs)

        # Check scope to highlight correct sidebar link
        scope = self.request.GET.get("scope", "")
        ctx["active_section"] = "my_appointments" if scope == "personal" else "appointments"

        from features.booking.models import Appointment
        from features.cabinet.selector.appointment_selectors import get_cabinet_appointments

        is_personal = scope == "personal" or not self.request.user.is_staff
        client_filter = ctx.get("cabinet_client") if is_personal else None
        status_filter = self.request.GET.get("status", "")
        date_filter = self.request.GET.get("date", "")

        log.debug(
            f"View: AppointmentsView | Action: Filtering | scope={scope} | status={status_filter} | date={date_filter}"
        )

        qs = get_cabinet_appointments(user=self.request.user, client_filter=client_filter, status_filter=status_filter)

        if date_filter == "today":
            qs = qs.filter(datetime_start__date=timezone.localdate())

        paginator = Paginator(qs, 20)
        page_num = self.request.GET.get("page", 1)
        ctx["page_obj"] = paginator.get_page(page_num)
        ctx["total_count"] = paginator.count
        ctx["status_filter"] = status_filter
        ctx["date_filter"] = date_filter
        ctx["status_choices"] = Appointment.STATUS_CHOICES

        log.info(f"View: AppointmentsView | Action: Success | total_found={paginator.count} | page={page_num}")
        return ctx

    def post(self, request, *args, **kwargs):
        """HTMX inline status update (Admin only) + Notifications."""
        if not request.user.is_staff:
            log.warning(f"View: AppointmentsView | Action: PostDenied | user={request.user.id} | reason=NotStaff")
            return JsonResponse({"status": "error", "message": "Forbidden"}, status=403)

        from django.shortcuts import get_object_or_404
        from features.booking.models import Appointment
        from features.cabinet.services.appointment_service import AppointmentService

        appt_id = request.POST.get("id")
        action = request.POST.get("action")  # approve, cancel, get_slots, propose

        log.info(
            f"View: AppointmentsView | Action: PostAction | appt_id={appt_id} | action={action} | user={request.user.id}"
        )

        appointment = get_object_or_404(Appointment, id=appt_id)

        try:
            # 1. GET SLOTS (AJAX helper for reschedule)
            if action == "get_slots":
                slots = AppointmentService.get_upcoming_slots(appointment)
                log.debug(f"View: AppointmentsView | Action: GetSlots | appt_id={appt_id} | slots_count={len(slots)}")
                return JsonResponse({"status": "ok", "slots": slots})

            # 2. APPROVE
            if action == "approve":
                AppointmentService.approve_appointment(appointment)
                log.info(f"View: AppointmentsView | Action: Approved | appt_id={appt_id}")

            # 3. REJECT (Cancel)
            elif action == "cancel":
                reason_code = request.POST.get("reason_code")
                reason_text = request.POST.get("reason_text", "")
                AppointmentService.cancel_appointment(appointment, reason_code, reason_text)
                log.info(f"View: AppointmentsView | Action: Cancelled | appt_id={appt_id} | reason={reason_code}")

            # 4. PROPOSE (Reschedule)
            elif action == "propose":
                slot_label = request.POST.get("slot_label")
                datetime_str = request.POST.get("datetime_str")  # Expected from the frontend form
                if datetime_str:
                    AppointmentService.propose_reschedule(appointment, datetime_str, slot_label)
                    log.info(
                        f"View: AppointmentsView | Action: ProposedReschedule | appt_id={appt_id} | slot={slot_label}"
                    )

            # 5. EDIT/SAVE
            else:
                new_status = request.POST.get("status")
                admin_notes = request.POST.get("admin_notes", "")
                AppointmentService.update_appointment(appointment, new_status, admin_notes)
                log.info(f"View: AppointmentsView | Action: Updated | appt_id={appt_id} | status={new_status}")

        except Exception as e:
            log.error(
                f"View: AppointmentsView | Action: ActionFailed | appt_id={appt_id} | action={action} | error={e}"
            )
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

        # RETURN HTMX PARTIAL OR JSON
        if request.headers.get("HX-Request"):
            from django.shortcuts import render

            log.debug(f"View: AppointmentsView | Action: HTMXResponse | appt_id={appt_id}")
            ctx = self.get_context_data()
            ctx["appt"] = appointment
            return render(request, "cabinet/appointments/includes/_appointment_card.html", ctx)

        return JsonResponse({"status": "ok"})
