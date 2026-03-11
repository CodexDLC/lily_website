"""Appointments view: Admin sees all, Client sees own."""

import contextlib
from datetime import date, timedelta

from core.logger import log
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import TemplateView
from features.booking.models import Appointment, AppointmentGroup, AppointmentGroupItem
from features.booking.selectors.wizard_v2 import get_slots_panel_context
from features.booking.services.utils.calendar_service import CalendarService
from features.booking.services.v2_booking_service import BookingV2Service
from features.cabinet.mixins import CabinetAccessMixin, HtmxCabinetMixin
from features.cabinet.selector.appointment_selectors import get_cabinet_appointments
from features.system.services.notification import NotificationService


class AppointmentsView(HtmxCabinetMixin, CabinetAccessMixin, TemplateView):
    template_name = "cabinet/crm/appointments/list.html"

    def get(self, request, *args, **kwargs):
        # HTMX Actions for loading partials (forms)
        action = request.GET.get("action")

        if not action:
            return super().get(request, *args, **kwargs)

        # --- 1. Group HTMX Actions (require group_id) ---
        if action in ["group_reschedule_form", "view_group"]:
            group_id = request.GET.get("group_id")
            group = get_object_or_404(AppointmentGroup, id=group_id)

            if action == "group_reschedule_form":
                first_item = group.items.all().order_by("order").first()
                if first_item:
                    return self._render_reschedule_form(
                        request, first_item.appointment, is_group=True, group_id=group_id
                    )

            if action == "view_group":
                return render(
                    request,
                    "cabinet/crm/appointments/includes/_group_large_card.html",
                    {"group": group, "is_admin": request.user.is_staff},
                )

        # --- 2. Single Appointment HTMX Actions (require id) ---
        appt_id = request.GET.get("id")
        if appt_id:
            appointment = get_object_or_404(Appointment, id=appt_id)

            if action == "confirm_form":
                return render(request, "cabinet/crm/appointments/includes/_action_confirm.html", {"appt": appointment})

            if action == "complete_form":
                return render(request, "cabinet/crm/appointments/includes/_action_complete.html", {"appt": appointment})

            if action == "cancel_form":
                return render(request, "cabinet/crm/appointments/includes/_action_cancel.html", {"appt": appointment})

            if action == "reschedule_form":
                return self._render_reschedule_form(request, appointment)

            if action == "view_card":
                return render(
                    request,
                    "cabinet/crm/appointments/includes/_appointment_card.html",
                    {"appt": appointment, "is_admin": request.user.is_staff},
                )

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """HTMX inline status update (Admin only)."""
        if not request.user.is_staff:
            return HttpResponse('<div class="alert alert-danger">Forbidden</div>', status=403)

        action = request.POST.get("action")
        log.info(f"AppointmentsView.post: action={action}")
        booking_service = BookingV2Service()

        try:
            # --- 1. Group Actions (Approve, Cancel, Complete, Resend) ---
            if action in ["approve_group", "cancel_group", "complete_group", "resend_group_notification"]:
                group_id = request.POST.get("group_id")
                group = get_object_or_404(AppointmentGroup, id=group_id)

                if action == "approve_group":
                    group.approve_all()
                    self._trigger_group_notification(group)
                elif action == "cancel_group":
                    group.cancel_all()
                elif action == "complete_group":
                    group.complete_all()
                elif action == "resend_group_notification":
                    self._trigger_group_notification(group)

                return render(
                    request,
                    "cabinet/crm/appointments/includes/_group_large_card.html",
                    {"group": group, "is_admin": True},
                )

            # --- 2. Group Reschedule ---
            if action == "reschedule_group":
                new_date_str = request.POST.get("new_date")
                new_time_str = request.POST.get("new_time")
                group_id = request.POST.get("group_id")

                if not (new_date_str and new_time_str and group_id):
                    return HttpResponse('<div class="alert alert-warning">Missing data for group reschedule</div>')

                group = get_object_or_404(AppointmentGroup, id=group_id)
                booking_service.reschedule_group(group.id, date.fromisoformat(new_date_str), new_time_str)
                self._trigger_group_notification(group)

                return render(
                    request,
                    "cabinet/crm/appointments/includes/_group_large_card.html",
                    {"group": group, "is_admin": True},
                )

            # --- 3. Single Appointment Reschedule ---
            if action in ["reschedule", "propose_reschedule"]:
                new_date_str = request.POST.get("new_date")
                new_time_str = request.POST.get("new_time")
                appt_id = request.POST.get("id")

                if not (new_date_str and new_time_str and appt_id):
                    return HttpResponse('<div class="alert alert-warning">Missing data for reschedule</div>')

                appointment = get_object_or_404(Appointment, id=appt_id)

                if action == "propose_reschedule":
                    from features.cabinet.services.appointment_service import AppointmentService

                    dt_str = f"{date.fromisoformat(new_date_str).strftime('%d.%m.%Y')} {new_time_str}"
                    AppointmentService.propose_reschedule(appointment, dt_str, dt_str)
                else:
                    booking_service.reschedule_single(appointment.id, date.fromisoformat(new_date_str), new_time_str)

                    if hasattr(appointment, "group_item"):
                        self._trigger_group_notification(appointment.group_item.group, event_type="confirmation")
                    else:
                        # For direct reschedule, send an updated confirmation, not a proposal
                        self._trigger_notification(appointment, event_type="confirmation")

                appointment.refresh_from_db()
                return render(
                    request,
                    "cabinet/crm/appointments/includes/_appointment_card.html",
                    {"appt": appointment, "is_admin": True},
                )

            # --- 4. Other Single Appointment Actions ---
            appt_id = request.POST.get("id")
            if not appt_id:
                return HttpResponse(f'<div class="alert alert-danger">Unknown action: {action}</div>')

            appointment = get_object_or_404(Appointment, id=appt_id)

            if action == "approve":
                notes = request.POST.get("admin_notes")
                if notes:
                    appointment.admin_notes = notes
                appointment.status = Appointment.STATUS_CONFIRMED
                appointment.save()
                self._trigger_notification(appointment, event_type="confirmation")

            elif action == "complete":
                price = request.POST.get("price")
                notes = request.POST.get("admin_notes")
                if price:
                    appointment.price_actual = price
                if notes:
                    appointment.admin_notes = notes
                appointment.status = Appointment.STATUS_COMPLETED
                appointment.save()

            elif action == "cancel":
                reason_code = request.POST.get("reason_code", "other")
                reason_text = request.POST.get("reason_text", "")
                appointment.cancel(reason=reason_code, note=reason_text)
                self._trigger_notification(
                    appointment, event_type="cancellation", extra_context={"reason_text": reason_text}
                )

            elif action == "no_show":
                appointment.status = Appointment.STATUS_NO_SHOW
                appointment.save()
                self._trigger_notification(appointment, event_type="no_show")

            elif action == "resend_notification":
                self._trigger_notification(appointment, event_type="auto")

            appointment.refresh_from_db()
            return render(
                request,
                "cabinet/crm/appointments/includes/_appointment_card.html",
                {"appt": appointment, "is_admin": True},
            )

        except Exception as e:
            log.error(f"AppointmentsView: Action Error | {e}")
            return HttpResponse(f'<div class="alert alert-danger">Error: {str(e)}</div>', status=200)

    def _trigger_group_notification(self, group: AppointmentGroup, event_type: str = "confirmation"):
        """Отправить групповое уведомление через NotificationService."""
        try:
            items = group.items.select_related("appointment__master", "appointment__service").order_by("order")
            target_lang = group.lang or "de"
            from django.utils import translation

            with translation.override(target_lang):
                context = {
                    "group_id": group.id,
                    "booking_date": group.booking_date.strftime("%d.%m.%Y"),
                    "total_price": float(sum(item.appointment.price for item in items)),
                    "total_duration": group.total_duration_minutes,
                    "notes": group.notes,
                    "items": [],
                }
                for item in items:
                    appt = item.appointment
                    local_dt = timezone.localtime(appt.datetime_start)
                    context["items"].append(
                        {
                            "appointment_id": appt.id,
                            "service_name": appt.service.title,
                            "master_name": appt.master.name,
                            "time": local_dt.strftime("%H:%M"),
                            "price": float(appt.price),
                            "duration": appt.duration_minutes,
                        }
                    )

            # Для конструктора админки это всегда подтверждение (Terminbestätigung)
            NotificationService.send_group_booking_confirmation(
                recipient_email=group.client.email,
                client_name=f"{group.client.first_name} {group.client.last_name}",
                recipient_phone=group.client.phone,
                context=context,
                lang=target_lang,
            )
            log.info(f"AppointmentsView: group notification ({event_type}) triggered for Group #{group.id}")
        except Exception as e:
            log.error(f"AppointmentsView: group notification error: {e}")

    def _trigger_notification(
        self, appointment: Appointment, event_type: str = "auto", extra_context: dict | None = None
    ):
        """Отправить одиночное уведомление через NotificationService."""
        try:
            # Авто-определение типа события по статусу записи
            if event_type == "auto":
                status_map = {
                    Appointment.STATUS_PENDING: "receipt",
                    Appointment.STATUS_CONFIRMED: "confirmation",
                    Appointment.STATUS_CANCELLED: "cancellation",
                    Appointment.STATUS_NO_SHOW: "no_show",
                    Appointment.STATUS_RESCHEDULE_PROPOSED: "reschedule",
                }
                event_type = status_map.get(appointment.status, "confirmation")

            target_lang = appointment.lang or "de"
            from django.utils import translation

            with translation.override(target_lang):
                local_dt = timezone.localtime(appointment.datetime_start)
                context = {
                    "id": appointment.id,
                    "service_name": appointment.service.title,
                    "master_name": appointment.master.name,
                    "datetime": local_dt.strftime("%d.%m.%Y %H:%M"),
                    "price": float(appointment.price),
                    "duration_minutes": appointment.duration_minutes,
                    "client_notes": appointment.client_notes or "",
                }

            if extra_context:
                context.update(extra_context)

            # Выбираем метод в зависимости от типа события
            if event_type == "receipt":
                NotificationService.send_booking_receipt(
                    recipient_email=appointment.client.email,
                    client_name=appointment.client.first_name,
                    recipient_phone=appointment.client.phone,
                    context=context,
                    lang=target_lang,
                )
            elif event_type == "confirmation":
                NotificationService.send_booking_confirmation(
                    recipient_email=appointment.client.email,
                    client_name=appointment.client.first_name,
                    recipient_phone=appointment.client.phone,
                    context=context,
                    lang=target_lang,
                )
            elif event_type == "cancellation":
                NotificationService.send_booking_cancellation(
                    recipient_email=appointment.client.email,
                    client_name=appointment.client.first_name,
                    recipient_phone=appointment.client.phone,
                    context=context,
                    lang=target_lang,
                )
            elif event_type == "no_show":
                NotificationService.send_booking_no_show(
                    recipient_email=appointment.client.email,
                    client_name=appointment.client.first_name,
                    recipient_phone=appointment.client.phone,
                    context=context,
                    lang=target_lang,
                )
            elif event_type == "reschedule":
                NotificationService.send_booking_reschedule(
                    recipient_email=appointment.client.email,
                    client_name=appointment.client.first_name,
                    recipient_phone=appointment.client.phone,
                    context=context,
                    lang=target_lang,
                )

            log.info(f"AppointmentsView: notification ({event_type}) triggered for Appointment #{appointment.id}")
        except Exception as e:
            log.error(f"AppointmentsView: notification error: {e}")

    def _render_reschedule_form(self, request, appointment, is_group=False, group_id=None):
        selected_date_str = request.GET.get("date")
        if selected_date_str:
            selected_date = date.fromisoformat(selected_date_str)
        else:
            selected_date = appointment.datetime_start.date()

        today = date.today()

        # We now generate a 14-day strip starting from 'today' to allow scrolling
        start = today

        calendar_days = []
        for i in range(14):
            d = start + timedelta(days=i)
            calendar_days.append(
                {"date": d.isoformat(), "day": d.day, "weekday": d.strftime("%a"), "is_selected": d == selected_date}
            )

        if is_group:
            group = get_object_or_404(AppointmentGroup, id=group_id)
            items = group.items.all().order_by("order")
            service_ids = [item.service_id for item in items]
            exclude_ids = [item.appointment_id for item in items]
        else:
            service_ids = [appointment.service_id]
            exclude_ids = [appointment.id]

        slots_ctx = get_slots_panel_context(
            selected_service_ids=service_ids, selected_date=selected_date, exclude_appointment_ids=exclude_ids
        )

        ctx = {
            "appt": appointment,
            "calendar_days": calendar_days,
            "selected_date": selected_date.isoformat(),
            "slots": slots_ctx["slots"],
            "is_group": is_group,
            "group_id": group_id,
        }

        template = "cabinet/crm/appointments/includes/_action_reschedule.html"
        if is_group:
            template = "cabinet/crm/appointments/includes/_group_reschedule_form.html"

        return render(request, template, ctx)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        view_mode = self.request.GET.get("mode", "solo")
        scope = self.request.GET.get("scope", "")

        ctx["active_section"] = "my_appointments" if scope == "personal" else "appointments"
        ctx["view_mode"] = view_mode

        is_personal = scope == "personal" or not self.request.user.is_staff
        client_filter = ctx.get("cabinet_client") if is_personal else None
        status_filter = self.request.GET.get("status", "")
        date_str = self.request.GET.get("date", "")
        group_id = self.request.GET.get("group_id")

        if date_str == "today":
            target_date = timezone.localdate()
            date_str = target_date.isoformat()
        elif date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                target_date = None
        else:
            target_date = None

        if view_mode == "groups":
            from django.db.models import Prefetch

            items_prefetch = Prefetch(
                "items",
                queryset=AppointmentGroupItem.objects.select_related(
                    "appointment__service", "appointment__master"
                ).order_by("order"),
            )

            qs = AppointmentGroup.objects.annotate(items_count=Count("items")).filter(items_count__gt=1)
            qs = qs.select_related("client").prefetch_related(items_prefetch)

            if client_filter:
                qs = qs.filter(client=client_filter)
            if status_filter:
                qs = qs.filter(status=status_filter)
            if target_date:
                qs = qs.filter(booking_date=target_date)
            if group_id:
                qs = qs.filter(pk=group_id)

            paginator = Paginator(qs, 10)
            page_obj = paginator.get_page(self.request.GET.get("page", 1))
        else:
            qs = get_cabinet_appointments(
                user=self.request.user, client_filter=client_filter, status_filter=status_filter
            ).prefetch_related("group_item__group")
            if target_date:
                qs = qs.filter(datetime_start__date=target_date)
            if group_id:
                qs = qs.filter(group_item__group_id=group_id)
                with contextlib.suppress(AppointmentGroup.DoesNotExist):
                    ctx["selected_group"] = AppointmentGroup.objects.get(id=group_id)

            paginator = Paginator(qs, 20)
            page_obj = paginator.get_page(self.request.GET.get("page", 1))

        now = timezone.localtime()
        calendar_data = CalendarService.get_calendar_month_data(
            year=now.year, month=now.month, selected_date=target_date
        )

        ctx.update(
            {
                "page_obj": page_obj,
                "status_choices": Appointment.STATUS_CHOICES,
                "calendar_days": calendar_data["days"],
                "month_label": calendar_data["month_label"],
                "selected_date": date_str,
                "is_admin": self.request.user.is_staff,
                "group_id": group_id,
                "status_filter": status_filter,
                "date_filter": date_str,
            }
        )
        return ctx
