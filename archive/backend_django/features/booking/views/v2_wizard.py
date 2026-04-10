"""
V2 Booking Wizard Views.

HTMX-compatible views for the V2 booking constructor.
Each action swaps a specific panel without full page reload.

URL pattern:
    POST /cabinet/booking/v2/wizard/  with action= parameter

Actions:
    select_services -- Step 1: update selected services list
    select_date     -- Step 2: show calendar for selected services
    select_time     -- Step 3: show available slots for date
    confirm         -- Step 4: show summary before final booking
    create          -- Final: create AppointmentGroup (DB write)

HTMX targets:
    #v2-wizard-panel -- main swappable container
"""

import contextlib
from datetime import date

from codex_tools.booking import BookingEngineError, NoAvailabilityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from features.booking.models.client import Client
from features.booking.selectors.wizard_v2 import (
    get_calendar_panel_context,
    get_services_panel_context,
    get_slots_panel_context,
    get_summary_context,
)
from features.booking.services.v2_booking_service import BookingV2Service


class BookingV2WizardView(View):
    """
    HTMX-совместимый вид для V2 конструктора записи.

    Каждый POST-запрос с параметром action= возвращает
    только фрагмент HTML для указанной панели.

    Сессия:
        booking_v2_services -- list[int] выбранных service_ids
        booking_v2_date     -- str ISO дата
        booking_v2_time     -- str "HH:MM"

    Templates:
        booking/v2/panel_services.html  -- шаг 1: выбор услуг
        booking/v2/panel_calendar.html  -- шаг 2: выбор даты
        booking/v2/panel_slots.html     -- шаг 3: выбор времени
        booking/v2/panel_summary.html   -- шаг 4: подтверждение
        booking/v2/success.html         -- успех
    """

    # Ключи сессии
    SESSION_SERVICES = "booking_v2_services"
    SESSION_DATE = "booking_v2_date"
    SESSION_TIME = "booking_v2_time"
    SESSION_CONTACT = "booking_v2_contact"  # {"name": ..., "phone": ...}

    def get(self, request: HttpRequest) -> HttpResponse:
        """Отображает начальное состояние конструктора (шаг 1)."""
        self._clear_session(request)
        ctx = get_services_panel_context()
        return render(request, "booking/v2/wizard.html", ctx)

    def post(self, request: HttpRequest) -> HttpResponse:
        """Обрабатывает переходы между шагами конструктора."""
        action = request.POST.get("action", "")

        handlers = {
            "select_services": self._handle_select_services,
            "select_date": self._handle_select_date,
            "select_time": self._handle_select_time,
            "confirm": self._handle_confirm,
            "create": self._handle_create,
            "reset": self._handle_reset,
        }

        handler = handlers.get(action)
        if not handler:
            return HttpResponse("Unknown action", status=400)

        return handler(request)

    # ---------------------------------------------------------------------------
    # Шаги конструктора
    # ---------------------------------------------------------------------------

    def _handle_select_services(self, request: HttpRequest) -> HttpResponse:
        """
        Шаг 1: клиент выбрал услуги.
        Сохраняем service_ids в сессию, показываем календарь.
        """
        service_ids = self._parse_service_ids(request)
        if not service_ids:
            ctx = get_services_panel_context()
            ctx["error"] = "Выберите хотя бы одну услугу."
            return render(request, "booking/v2/panel_services.html", ctx)

        request.session[self.SESSION_SERVICES] = service_ids
        ctx = get_calendar_panel_context(service_ids)
        return render(request, "booking/v2/panel_calendar.html", ctx)

    def _handle_select_date(self, request: HttpRequest) -> HttpResponse:
        """
        Шаг 2: клиент выбрал дату.
        Показываем доступные слоты для услуг на эту дату.
        """
        date_str = request.POST.get("date", "")
        service_ids = request.session.get(self.SESSION_SERVICES, [])

        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            return HttpResponse("Invalid date", status=400)

        request.session[self.SESSION_DATE] = date_str
        ctx = get_slots_panel_context(
            selected_service_ids=service_ids,
            selected_date=selected_date,
        )
        return render(request, "booking/v2/panel_slots.html", ctx)

    def _handle_select_time(self, request: HttpRequest) -> HttpResponse:
        """
        Шаг 3: клиент выбрал время.
        Показываем финальный summary для подтверждения.
        """
        selected_time = request.POST.get("time", "")
        service_ids = request.session.get(self.SESSION_SERVICES, [])
        date_str = request.session.get(self.SESSION_DATE, "")

        if not selected_time or not date_str:
            return HttpResponse("Session expired, please restart.", status=400)

        request.session[self.SESSION_TIME] = selected_time

        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            return HttpResponse("Invalid date in session", status=400)

        ctx = get_summary_context(
            selected_service_ids=service_ids,
            selected_date=selected_date,
            selected_time=selected_time,
        )
        return render(request, "booking/v2/panel_summary.html", ctx)

    def _handle_confirm(self, request: HttpRequest) -> HttpResponse:
        """Шаг 4: показать ещё раз summary с кнопкой подтверждения."""
        service_ids = request.session.get(self.SESSION_SERVICES, [])
        date_str = request.session.get(self.SESSION_DATE, "")
        selected_time = request.session.get(self.SESSION_TIME, "")

        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            return redirect("booking:v2_wizard")

        ctx = get_summary_context(service_ids, selected_date, selected_time)
        ctx["confirm_mode"] = True
        return render(request, "booking/v2/panel_summary.html", ctx)

    def _handle_create(self, request: HttpRequest) -> HttpResponse:
        """
        Финальный шаг: создаём бронирование.

        Вызывает BookingV2Service.create_group() внутри transaction.atomic.
        При успехе -- редирект на страницу успеха.
        При ошибке -- показываем понятное сообщение, возвращаем к слотам.
        """
        service_ids = request.session.get(self.SESSION_SERVICES, [])
        date_str = request.session.get(self.SESSION_DATE, "")
        selected_time = request.session.get(self.SESSION_TIME, "")

        if not (service_ids and date_str and selected_time):
            return redirect("booking:v2_wizard")

        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            return redirect("booking:v2_wizard")

        # Для гостей — сохраняем контакт из POST в сессию
        if not request.user.is_authenticated:
            request.session[self.SESSION_CONTACT] = {
                "name": request.POST.get("guest_name", "Гость"),
                "phone": request.POST.get("guest_phone", ""),
                "email": request.POST.get("guest_email", ""),
            }

        client = self._get_or_create_client(request)

        try:
            svc = BookingV2Service()
            group = svc.create_group(
                client=client,
                service_ids=service_ids,
                target_date=selected_date,
                selected_start_time=selected_time,
            )
        except NoAvailabilityError as e:
            # Слот пропал между выбором и подтверждением
            ctx = get_slots_panel_context(service_ids, selected_date)
            ctx["error"] = str(e)
            return render(request, "booking/v2/panel_slots.html", ctx)
        except BookingEngineError as e:
            ctx = get_summary_context(service_ids, selected_date, selected_time)
            ctx["error"] = str(e)
            return render(request, "booking/v2/panel_summary.html", ctx)

        self._clear_session(request)
        return render(request, "booking/v2/success.html", {"group": group})

    def _handle_reset(self, request: HttpRequest) -> HttpResponse:
        """Сброс конструктора -- возврат к шагу 1."""
        self._clear_session(request)
        ctx = get_services_panel_context()
        return render(request, "booking/v2/panel_services.html", ctx)

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def _clear_session(self, request: HttpRequest) -> None:
        """Очищает V2 данные из сессии."""
        for key in (self.SESSION_SERVICES, self.SESSION_DATE, self.SESSION_TIME, self.SESSION_CONTACT):
            request.session.pop(key, None)

    @staticmethod
    def _parse_service_ids(request: HttpRequest) -> list[int]:
        """Парсит список service_ids из POST (checkbox[] или JSON)."""
        raw = request.POST.getlist("service_ids")
        result = []
        for val in raw:
            with contextlib.suppress(ValueError, TypeError):
                result.append(int(val))
        return result

    def _get_or_create_client(self, request: HttpRequest) -> Client:
        """
        Возвращает или создаёт Client.

        Для залогиненных: берём по user.
        Для гостей: берём контакт из сессии (SESSION_CONTACT).
        """
        user = request.user
        if user.is_authenticated:
            client, _ = Client.objects.get_or_create(
                user=user,
                defaults={
                    "name": user.get_full_name() or user.email,
                    "email": user.email,
                    "phone": "",
                },
            )
            return client

        # Гость — данные из сессии (собираются на шаге summary)
        contact = request.session.get(self.SESSION_CONTACT, {})
        name = contact.get("name", "Гость")
        phone = contact.get("phone", "")
        email = contact.get("email", "")

        # Ищем по телефону или создаём нового
        if phone:
            client, _ = Client.objects.get_or_create(
                phone=phone,
                defaults={"name": name, "email": email},
            )
        else:
            client = Client.objects.create(name=name, email=email, phone="")

        return client
