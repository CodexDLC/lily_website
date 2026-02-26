"""Cabinet: Create new appointment (Admin only)."""

import json
from datetime import date, datetime, timedelta

from core.logger import log
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView
from features.booking.models import Appointment, Client, Master
from features.booking.services.client_service import ClientService
from features.booking.services.slots import SlotService
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.main.models.service import Service

slot_service = SlotService()


class AppointmentCreateView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/appointments/create.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "appointments_create"
        ctx["masters"] = Master.objects.filter(status="active").order_by("order")
        ctx["services"] = Service.objects.filter(is_active=True).order_by("category__order", "order")
        return ctx

    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "search_clients":
            return self._search_clients(request)
        if action == "get_client_status":
            return self._get_client_status(request)
        if action == "get_services":
            return self._get_services(request)
        if action == "get_dates":
            return self._get_dates(request)
        if action == "get_slots":
            return self._get_slots(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._create_appointment(request)

    # --- HTMX: client search ---
    def _search_clients(self, request):
        q = request.GET.get("q", "").strip()
        if len(q) < 2:
            return HttpResponse("")

        q_norm = ClientService._normalize_phone(q)
        query = models.Q(first_name__icontains=q) | models.Q(last_name__icontains=q)
        if q_norm:
            query |= models.Q(phone__icontains=q_norm)
        if "@" in q:
            query |= models.Q(email__icontains=q)

        clients = Client.objects.filter(query).order_by("-updated_at")[:6]
        if not clients:
            return HttpResponse(
                '<div class="search-result-item"><span class="create-hint">Ничего не найдено</span></div>'
            )

        html = ""
        for c in clients:
            html += (
                f'<div class="search-result-item" onclick="fillClientData({{'
                f"phone:'{c.phone}',first_name:'{c.first_name}',"
                f"last_name:'{c.last_name}',email:'{c.email}',"
                f"instagram:'{c.instagram}',telegram:'{c.telegram}',id:'{c.id}'"
                f'}})">'
                f'<div class="search-name">{c.display_name()}</div>'
                f'<div class="search-phone">{c.phone}</div>'
                f"</div>"
            )
        return HttpResponse(html)

    # --- HTMX: client history badge ---
    def _get_client_status(self, request):
        client_id = request.GET.get("client_id")
        if not client_id:
            return HttpResponse("")
        try:
            client = Client.objects.get(id=client_id)
            future = (
                Appointment.objects.filter(client=client, datetime_start__gt=timezone.now())
                .exclude(status=Appointment.STATUS_CANCELLED)
                .count()
            )
            past = Appointment.objects.filter(client=client, datetime_start__lt=timezone.now()).count()
            html = '<div class="client-badge">'
            if future > 0:
                html += f'<div class="badge-warning">⚠️ Уже есть {future} будущих записей!</div>'
            html += f'<div class="badge-info">📜 Прошлых визитов: {past}</div>'
            html += "</div>"
            return HttpResponse(html)
        except Client.DoesNotExist:
            return HttpResponse("")
        except Exception as e:
            log.error(f"Cabinet get_client_status error: {e}")
            return HttpResponse("")

    # --- HTMX: services for master ---
    def _get_services(self, request):
        master_id = request.GET.get("master_id")
        services = Service.objects.filter(is_active=True).order_by("category__order", "order")
        if master_id and master_id != "any":
            try:
                master = Master.objects.get(id=master_id)
                services = services.filter(category__in=master.categories.all())
            except Master.DoesNotExist:
                pass
        html = '<option value="" disabled selected>Выберите услугу...</option>'
        for s in services:
            html += f'<option value="{s.id}">{s.title} ({s.duration} мин)</option>'
        return HttpResponse(html)

    # --- HTMX: available dates ---
    def _get_dates(self, request):
        master_id = request.GET.get("master_id")
        service_id = request.GET.get("service_id")
        if not service_id:
            return HttpResponse("")
        try:
            service = Service.objects.get(id=service_id)
            masters = (
                [Master.objects.get(id=master_id)]
                if master_id and master_id != "any"
                else list(Master.objects.filter(status="active", categories=service.category))
            )
            available_dates = []
            today = timezone.localdate()
            ru_months = {
                1: "Янв",
                2: "Фев",
                3: "Мар",
                4: "Апр",
                5: "Май",
                6: "Июн",
                7: "Июл",
                8: "Авг",
                9: "Сен",
                10: "Окт",
                11: "Ноя",
                12: "Дек",
            }
            ru_days = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}

            for offset in range(-7, 45):
                check_date = today + timedelta(days=offset)
                slots = slot_service.get_available_slots(masters, check_date, service.duration, allow_past=True)
                if slots:
                    available_dates.append(
                        {
                            "iso": check_date.isoformat(),
                            "day": check_date.day,
                            "month": ru_months[check_date.month],
                            "weekday": ru_days[check_date.weekday()],
                        }
                    )
                if len(available_dates) >= 25:
                    break

            html = ""
            for d in available_dates:
                html += (
                    f'<div class="date-bubble" onclick="selectDate(\'{d["iso"]}\', this)">'
                    f'<span class="weekday">{d["weekday"]}</span>'
                    f'<span class="day-num">{d["day"]}</span>'
                    f'<span class="month-name">{d["month"]}</span>'
                    f"</div>"
                )
            return HttpResponse(html if html else '<p class="create-hint">Нет доступных дат</p>')
        except Exception as e:
            log.error(f"Cabinet get_dates error: {e}")
            return HttpResponse("Ошибка", status=500)

    # --- HTMX: available slots ---
    def _get_slots(self, request):
        master_id = request.GET.get("master_id")
        service_id = request.GET.get("service_id")
        date_str = request.GET.get("date")
        if not all([service_id, date_str]):
            return HttpResponse("")
        try:
            service = Service.objects.get(id=service_id)
            date_obj = date.fromisoformat(date_str)
            masters = (
                [Master.objects.get(id=master_id)]
                if master_id and master_id != "any"
                else list(Master.objects.filter(status="active", categories=service.category))
            )
            slots = slot_service.get_available_slots(masters, date_obj, service.duration, allow_past=True)
            html = ""
            for s in slots:
                html += f'<div class="time-pill" onclick="selectTime(\'{s}\', this)">{s}</div>'
            return HttpResponse(html if html else '<p class="create-hint">Мест нет</p>')
        except Exception as e:
            log.error(f"Cabinet get_slots error: {e}")
            return HttpResponse("Ошибка", status=500)

    # --- POST: create appointment ---
    def _create_appointment(self, request):
        try:
            data = json.loads(request.body)
            phone = data.get("phone", "").strip()
            if not phone:
                phone = f"ghost-{timezone.now().timestamp()}"

            client = ClientService.get_or_create_client(
                first_name=data.get("first_name", "").strip(),
                last_name=data.get("last_name", "").strip(),
                phone=phone,
                email=data.get("email", "").strip(),
                instagram=data.get("instagram", "").strip(),
                telegram=data.get("telegram", "").strip(),
                consent_marketing=data.get("consent_marketing", False),
            )
            service = Service.objects.get(id=data.get("service_id"))
            master = (
                Master.objects.get(id=data.get("master_id"))
                if data.get("master_id") != "any"
                else Master.objects.filter(status="active", categories=service.category).first()
            )
            dt = timezone.make_aware(datetime.fromisoformat(data.get("datetime_start")))

            appointment = Appointment.objects.create(
                client=client,
                master=master,
                service=service,
                datetime_start=dt,
                duration_minutes=service.duration,
                price=service.price,
                status=Appointment.STATUS_CONFIRMED,
                source=Appointment.SOURCE_ADMIN,
                client_notes=data.get("client_notes", "").strip(),
                admin_notes=data.get("admin_notes", "").strip(),
            )

            try:
                from core.arq.client import DjangoArqClient
                from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

                NotificationCacheManager.seed_appointment(appointment.id, extra_data={"is_admin_booking": True})
                DjangoArqClient.enqueue_job("send_booking_notification_task", appointment_id=appointment.id)
            except Exception as e:
                log.error(f"Cabinet notification error: {e}")

            log.info(f"Cabinet Admin Created: {client.display_name()} | {master.name} | {service.title}")
            return JsonResponse({"status": "success"})
        except Exception as e:
            log.error(f"Cabinet create appointment error: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
