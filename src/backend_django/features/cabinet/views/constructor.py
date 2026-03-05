"""V2 Booking Constructor for Admin (Complex Bookings)."""

import contextlib
from datetime import date, datetime

from codex_tools.booking import BookingEngineError, BookingMode, NoAvailabilityError
from codex_tools.common.phone import normalize_phone
from core.logger import log
from django.db import models, transaction
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import TemplateView
from features.booking.models import Appointment, AppointmentGroup, AppointmentGroupItem
from features.booking.models.client import Client
from features.booking.models.master import Master
from features.booking.models.master_day_off import MasterDayOff
from features.booking.selectors.wizard_v2 import (
    get_calendar_panel_context,
    get_slots_panel_context,
)
from features.booking.services.booking import BookingService
from features.booking.services.utils.client_service import ClientService
from features.booking.services.v2_booking_service import BookingV2Service
from features.cabinet.mixins import AdminRequiredMixin, HtmxCabinetMixin
from features.main.models.category import Category
from features.main.models.service import Service


class AdminConstructorView(HtmxCabinetMixin, AdminRequiredMixin, TemplateView):
    template_name = "cabinet/crm/constructor/index.html"

    SESSION_KEY = "admin_constructor_services"
    SESSION_MASTERS = "admin_constructor_masters"
    SESSION_DATE = "admin_constructor_date"
    SESSION_TIME = "admin_constructor_time"  # complex mode: выбранное время
    SESSION_MODE = "admin_constructor_mode"  # 'complex' or 'separate'
    SESSION_ACTIVE_IDX = "admin_constructor_active_idx"
    SESSION_SLOTS = "admin_constructor_slots"  # {idx: {"date": "...", "time": "..."}}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_section"] = "constructor"

        ctx["current_category"] = self.request.POST.get("category", "all")

        # Block 1: All Services
        ctx["categories"] = Category.objects.filter(is_active=True).order_by("order")
        ctx["services"] = Service.objects.filter(is_active=True).select_related("category").order_by("order")

        # Block 2: Selected Services & Masters
        service_ids = self.request.session.get(self.SESSION_KEY, [])
        ctx["selected_service_ids"] = service_ids

        selected_masters = self.request.session.get(self.SESSION_MASTERS, {})

        services_qs = Service.objects.filter(id__in=service_ids).select_related("category")
        services_map = {s.id: s for s in services_qs}

        # Prefetch categories once, then build lookup to avoid N+1
        all_active_masters = list(
            Master.objects.filter(status=Master.STATUS_ACTIVE).prefetch_related("categories").order_by("order")
        )
        master_category_ids: dict[int, set[int]] = {
            m.pk: set(m.categories.values_list("id", flat=True)) for m in all_active_masters
        }

        ordered_services = []
        for idx, s_id in enumerate(service_ids):
            svc = services_map.get(s_id)
            if svc:
                svc.temp_idx = idx
                svc.selected_master_id = selected_masters.get(str(idx), "any")
                svc.suitable_masters = [m for m in all_active_masters if svc.category_id in master_category_ids[m.pk]]
                ordered_services.append(svc)

        ctx["selected_services"] = ordered_services
        ctx["total_duration"] = sum(s.duration for s in ordered_services)

        ctx["mode"] = self.request.session.get(self.SESSION_MODE, "complex")
        ctx["active_idx"] = int(self.request.session.get(self.SESSION_ACTIVE_IDX, 0))
        ctx["service_slots"] = self.request.session.get(self.SESSION_SLOTS, {})

        # Block 3: Calendar
        active_service_ids = service_ids
        if ctx["mode"] == "separate" and 0 <= ctx["active_idx"] < len(service_ids):
            active_service_ids = [service_ids[ctx["active_idx"]]]

        current_date_str = self.request.session.get(self.SESSION_DATE)
        if ctx["mode"] == "separate":
            slot_data = ctx["service_slots"].get(str(ctx["active_idx"]))
            if slot_data:
                current_date_str = slot_data.get("date")

        current_date_obj: date | None = None
        if current_date_str:
            with contextlib.suppress(ValueError):
                current_date_obj = date.fromisoformat(current_date_str)

        calendar_ctx = get_calendar_panel_context(
            active_service_ids,
            selected_date=current_date_obj,
        )
        ctx.update(calendar_ctx)
        ctx["selected_date"] = current_date_str

        # Confirmation eligibility
        can_confirm = False
        if ctx["mode"] == "separate":
            if service_ids:
                is_all_set = True
                for i in range(len(service_ids)):
                    slot = ctx["service_slots"].get(str(i))
                    if not slot or not slot.get("time"):
                        is_all_set = False
                        break
                can_confirm = is_all_set
        else:
            # Complex mode: нужна дата И время (оба в сессии)
            date_str = self.request.session.get(self.SESSION_DATE)
            time_str = self.request.session.get(self.SESSION_TIME)
            can_confirm = bool(service_ids and date_str and time_str)

        ctx["can_confirm"] = can_confirm
        ctx["selected_time"] = self.request.session.get(self.SESSION_TIME)

        return ctx

    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "search_clients":
            return self._search_clients(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        service_ids = request.session.get(self.SESSION_KEY, [])
        selected_masters = request.session.get(self.SESSION_MASTERS, {})

        if action == "add_service":
            try:
                svc_id = int(request.POST.get("service_id"))
            except (TypeError, ValueError):
                return HttpResponse("Invalid service_id", status=400)
            service_ids.append(svc_id)
            request.session[self.SESSION_KEY] = service_ids
            return self._render_blocks(request)

        elif action == "remove_service":
            try:
                idx = int(request.POST.get("idx"))
            except (TypeError, ValueError):
                return HttpResponse("Invalid idx", status=400)
            if 0 <= idx < len(service_ids):
                service_ids.pop(idx)
                new_masters = {}
                for k, v in selected_masters.items():
                    k_int = int(k)
                    if k_int < idx:
                        new_masters[k] = v
                    elif k_int > idx:
                        new_masters[str(k_int - 1)] = v
                request.session[self.SESSION_KEY] = service_ids
                request.session[self.SESSION_MASTERS] = new_masters
            return self._render_blocks(request)

        elif action == "move_service":
            try:
                idx = int(request.POST.get("idx"))
            except (TypeError, ValueError):
                return HttpResponse("Invalid idx", status=400)
            direction = request.POST.get("direction")
            if 0 <= idx < len(service_ids):
                new_idx = idx - 1 if direction == "up" else idx + 1
                if 0 <= new_idx < len(service_ids):
                    service_ids[idx], service_ids[new_idx] = service_ids[new_idx], service_ids[idx]
                    idx_str, new_idx_str = str(idx), str(new_idx)
                    m1 = selected_masters.get(idx_str)
                    m2 = selected_masters.get(new_idx_str)
                    if m1:
                        selected_masters[new_idx_str] = m1
                    else:
                        selected_masters.pop(new_idx_str, None)
                    if m2:
                        selected_masters[idx_str] = m2
                    else:
                        selected_masters.pop(idx_str, None)
                    request.session[self.SESSION_KEY] = service_ids
                    request.session[self.SESSION_MASTERS] = selected_masters
            return self._render_blocks(request)

        elif action == "select_master":
            idx = request.POST.get("idx")
            master_id = request.POST.get("master_id")
            selected_masters[str(idx)] = master_id
            request.session[self.SESSION_MASTERS] = selected_masters
            date_str = request.session.get(self.SESSION_DATE)
            if date_str:
                return self._render_slots(request, date_str)
            return HttpResponse(status=204)

        elif action == "select_date":
            date_str = request.POST.get("date")
            mode = request.session.get(self.SESSION_MODE, "complex")

            if mode == "complex":
                request.session[self.SESSION_DATE] = date_str
                # Смена даты — сбросить время
                request.session.pop(self.SESSION_TIME, None)
            else:
                active_idx_val = request.session.get(self.SESSION_ACTIVE_IDX, 0)
                idx_key = str(active_idx_val)
                slots = request.session.get(self.SESSION_SLOTS, {})
                if idx_key not in slots:
                    slots[idx_key] = {}
                slots[idx_key]["date"] = date_str
                slots[idx_key]["time"] = None
                request.session[self.SESSION_SLOTS] = slots

            return self._render_slots(request, date_str)

        elif action == "select_time":
            time_val = request.POST.get("time")
            mode = request.session.get(self.SESSION_MODE, "complex")

            if mode == "separate":
                active_idx_val = request.session.get(self.SESSION_ACTIVE_IDX, 0)
                idx_key = str(active_idx_val)
                slots = request.session.get(self.SESSION_SLOTS, {})
                if idx_key in slots:
                    slots[idx_key]["time"] = time_val
                    request.session[self.SESSION_SLOTS] = slots
            else:
                # Complex mode: сохранить время в сессию
                request.session[self.SESSION_TIME] = time_val
                log.debug("Constructor: select_time [complex] → {}", time_val)

            return self._render_blocks(request)

        elif action == "set_mode":
            mode = request.POST.get("mode", "complex")
            request.session[self.SESSION_MODE] = mode
            return self._render_blocks(request)

        elif action == "set_active_service":
            try:
                idx_val = int(request.POST.get("idx", "0"))
            except (TypeError, ValueError):
                idx_val = 0
            request.session[self.SESSION_ACTIVE_IDX] = idx_val
            return self._render_blocks(request)

        elif action == "create_booking":
            return self._create_booking(request)

        elif action == "reset":
            for key in (
                self.SESSION_KEY,
                self.SESSION_MASTERS,
                self.SESSION_DATE,
                self.SESSION_TIME,
                self.SESSION_MODE,
                self.SESSION_ACTIVE_IDX,
                self.SESSION_SLOTS,
            ):
                request.session.pop(key, None)
            return render(request, self.template_name, self.get_context_data())

        return HttpResponse("Invalid action", status=400)

    def _search_clients(self, request):
        q = request.GET.get("q", "").strip()
        if len(q) < 2:
            return HttpResponse("")
        q_norm = normalize_phone(q)
        query = models.Q(first_name__icontains=q) | models.Q(last_name__icontains=q) | models.Q(email__icontains=q)
        if q_norm:
            query |= models.Q(phone__icontains=q_norm)
        clients = Client.objects.filter(query).order_by("-updated_at")[:5]
        return render(
            request,
            "cabinet/crm/constructor/includes/_client_results.html",
            {"clients": clients},
        )

    def _render_blocks(self, request):
        ctx = self.get_context_data()
        return render(request, "cabinet/crm/constructor/index.html", ctx)

    def _render_slots(self, request, date_str):
        mode = request.session.get(self.SESSION_MODE, "complex")
        service_ids = request.session.get(self.SESSION_KEY, [])
        selected_masters = request.session.get(self.SESSION_MASTERS, {})

        if mode == "separate":
            idx_obj = request.session.get(self.SESSION_ACTIVE_IDX, 0)
            try:
                idx = int(idx_obj)
            except (TypeError, ValueError):
                idx = 0
            if 0 <= idx < len(service_ids):
                service_ids = [service_ids[idx]]

        log.debug(
            "Constructor._render_slots: mode={} service_ids={} date={} masters={}",
            mode,
            service_ids,
            date_str,
            selected_masters,
        )

        try:
            selected_date = date.fromisoformat(date_str)
            slots_ctx = get_slots_panel_context(
                service_ids,
                selected_date,
                mode=mode,
                master_selections=selected_masters,
            )
            return render(
                request,
                "cabinet/crm/constructor/includes/_slots_grid.html",
                slots_ctx,
            )
        except ValueError:
            return HttpResponse("Invalid date", status=400)

    def _create_booking(self, request):
        service_ids = request.session.get(self.SESSION_KEY, [])
        if not service_ids:
            return HttpResponse("No services selected", status=400)

        phone = request.POST.get("phone")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        notes = request.POST.get("notes", "")

        if not phone and not email:
            return HttpResponse("Phone or Email is required", status=400)

        log.info(
            "Constructor._create_booking START | mode={} | services={} | phone={}",
            request.session.get(self.SESSION_MODE, "complex"),
            service_ids,
            phone,
        )

        client = ClientService.get_or_create_client(
            phone=phone, email=email, first_name=first_name, last_name=last_name
        )
        mode = request.session.get(self.SESSION_MODE, "complex")
        booking_service = BookingV2Service()

        try:
            with transaction.atomic():
                if mode == "complex":
                    group = self._create_complex(request, client, booking_service, service_ids, notes)
                else:
                    group = self._create_separate(request, client, service_ids, notes)

            return HttpResponse(f'<div class="alert alert-success">Booking #{group.pk} created successfully!</div>')

        except (NoAvailabilityError, BookingEngineError) as e:
            log.warning("Constructor._create_booking: Availability Error | {}", e)
            return HttpResponse(
                f'<div class="alert alert-warning">⚠️ {str(e)}</div>',
                status=200,  # Return 200 so HTMX renders it, but show warning style
            )
        except Exception as e:
            log.error("Constructor._create_booking ERROR | mode={} | services={} | {}", mode, service_ids, e)
            return HttpResponse(
                f'<div class="alert alert-danger">Error: {str(e)}</div>',
                status=400,
            )

    def _create_complex(self, request, client, booking_service, service_ids, notes):
        """Complex mode: все услуги через BookingV2Service (движок подбирает цепочку)."""
        date_str = request.session.get(self.SESSION_DATE)
        time_val = request.session.get(self.SESSION_TIME)
        if not date_str or not time_val:
            raise ValueError("Date or time not selected")

        selected_masters = request.session.get(self.SESSION_MASTERS, {})
        log.debug(
            "Constructor._create_complex: date={} time={} masters={}",
            date_str,
            time_val,
            selected_masters,
        )

        group = booking_service.create_group(
            client=client,
            service_ids=service_ids,
            target_date=date.fromisoformat(date_str),
            selected_start_time=time_val,
            mode=BookingMode.SINGLE_DAY,
            notes=notes,
            master_selections=selected_masters,
            source=Appointment.SOURCE_ADMIN,
            initial_status=Appointment.STATUS_CONFIRMED,  # Auto-confirm admin bookings
        )

        # Trigger unified group notification
        self._trigger_group_notification(group)

        log.info(
            "Constructor._create_complex: AppointmentGroup #{} | client={} | services={}",
            group.pk,
            client.pk,
            service_ids,
        )
        return group

    def _create_separate(self, request, client, service_ids, notes):
        """Separate mode: каждая услуга со своей датой/временем, без движка."""
        slots = request.session.get(self.SESSION_SLOTS, {})
        selected_masters = request.session.get(self.SESSION_MASTERS, {})

        services = Service.objects.filter(id__in=service_ids)
        svc_map = {s.id: s for s in services}

        total_dur = sum(svc_map[sid].duration for sid in service_ids if sid in svc_map)

        # Определить дату группы по первому слоту (не date.today())
        first_slot = next(
            (slots[str(i)] for i in range(len(service_ids)) if str(i) in slots),
            None,
        )
        try:
            group_date = date.fromisoformat(first_slot["date"]) if first_slot else date.today()
        except (KeyError, ValueError):
            group_date = date.today()

        group = AppointmentGroup.objects.create(
            client=client,
            booking_date=group_date,
            status=AppointmentGroup.STATUS_CONFIRMED,  # Auto-confirm
            engine_mode=BookingMode.SEPARATE.value,
            total_duration_minutes=total_dur,
            notes=notes,
        )
        log.debug(
            "Constructor._create_separate: AppointmentGroup #{} | booking_date={}",
            group.pk,
            group_date,
        )

        for i, svc_id in enumerate(service_ids):
            idx_key = str(i)
            slot = slots.get(idx_key)
            if not slot or not slot.get("date") or not slot.get("time"):
                raise ValueError(f"Missing date/time for service #{i + 1}")

            target_date = date.fromisoformat(slot["date"])
            target_time = datetime.strptime(slot["time"], "%H:%M").time()
            dt_start = timezone.make_aware(datetime.combine(target_date, target_time))

            service = svc_map.get(svc_id)
            if not service:
                raise ValueError(f"Service id={svc_id} not found")

            master_id = selected_masters.get(idx_key)
            log.debug(
                "Constructor._create_separate: service #{} id={} | date={} | time={} | master_id={}",
                i,
                svc_id,
                slot["date"],
                slot["time"],
                master_id,
            )

            master = self._resolve_master(service, master_id, target_date, dt_start)

            # Проверка конфликта (SELECT FOR UPDATE внутри transaction.atomic)
            if not BookingService._is_slot_still_available(
                master=master,
                start_dt=dt_start,
                duration_minutes=service.duration,
                for_update=True,
            ):
                log.warning(
                    "Constructor._create_separate: CONFLICT | master={} (id={}) | dt={}",
                    master.name,
                    master.pk,
                    dt_start,
                )
                raise ValueError(
                    f"Мастер {master.name} уже занят в {slot['time']} — "
                    f"выберите другое время для услуги «{service.title}»"
                )

            appointment = Appointment.objects.create(
                client=client,
                master=master,
                service=service,
                datetime_start=dt_start,
                duration_minutes=service.duration,
                status=Appointment.STATUS_CONFIRMED,  # Auto-confirm
                source=Appointment.SOURCE_ADMIN,
            )
            log.debug(
                "Constructor._create_separate: Appointment #{} | master={} | service={} | dt={}",
                appointment.pk,
                master.name,
                service.title,
                dt_start,
            )

            AppointmentGroupItem.objects.create(
                group=group,
                appointment=appointment,
                service=service,
                order=i,
            )

        # Trigger unified group notification
        self._trigger_group_notification(group)

        log.info(
            "Constructor._create_separate: AppointmentGroup #{} done | client={} | services={}",
            group.pk,
            client.pk,
            service_ids,
        )
        return group

    def _resolve_master(self, service, master_id, target_date: date, dt_start) -> Master:
        """
        Возвращает мастера для записи.
        """
        if master_id and master_id != "any":
            try:
                return Master.objects.get(pk=master_id)
            except Master.DoesNotExist as err:
                raise ValueError(f"Master id={master_id} not found") from err

        # "Any master": перебираем кандидатов, проверяем реальную доступность
        candidates = Master.objects.filter(
            categories=service.category,
            status=Master.STATUS_ACTIVE,
        ).order_by("order")

        for candidate in candidates:
            if target_date.weekday() not in (candidate.work_days or []):
                continue
            if MasterDayOff.objects.filter(master=candidate, date=target_date).exists():
                continue
            if BookingService._is_slot_still_available(
                master=candidate,
                start_dt=dt_start,
                duration_minutes=service.duration,
                for_update=True,
            ):
                return candidate

        raise ValueError(
            f"Нет доступного мастера для «{service.title}» на {target_date} в {dt_start.strftime('%H:%M')}"
        )

    def _trigger_group_notification(self, group: AppointmentGroup):
        """Отправить групповое уведомление боту через ARQ."""
        try:
            from core.arq.client import DjangoArqClient
            from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

            # Seed the unified group data to Redis
            NotificationCacheManager.seed_group_appointment(group.id, extra_data={"is_admin_booking": True})

            # Enqueue the NEW group task
            DjangoArqClient.enqueue_job("send_group_booking_notification_task", group_id=group.id)
            log.info("Constructor: group notification triggered for Group #{}", group.id)
        except Exception as e:
            log.error("Constructor: group notification error for Group #{}: {}", group.id, e)

    def _trigger_notification(self, appointment: Appointment):
        """Отправить уведомление боту через ARQ (Solo - legacy/fallback)."""
        try:
            from core.arq.client import DjangoArqClient
            from features.system.redis_managers.notification_cache_manager import NotificationCacheManager

            NotificationCacheManager.seed_appointment(appointment.id, extra_data={"is_admin_booking": True})
            DjangoArqClient.enqueue_job("send_booking_notification_task", appointment_id=appointment.id)
            log.info("Constructor: notification triggered for Appointment #{}", appointment.id)
        except Exception as e:
            log.error("Constructor: notification error for Appointment #{}: {}", appointment.id, e)
