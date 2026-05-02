"""Booking commit view — creates appointments from cart."""

from __future__ import annotations

import datetime
from decimal import ROUND_HALF_UP, Decimal

from core.logger import logger
from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from system.models import Client

from features.booking.dto.public_cart import clear_cart, get_cart, save_cart
from features.booking.models import AppointmentGroup, AppointmentGroupItem
from features.booking.selector.engine import get_booking_engine_gateway
from features.main.models import ServiceCombo


def _get_or_create_client(first_name: str, last_name: str, phone: str, email: str) -> Client:
    """Find or create a ghost Client from contact data."""
    # Try phone first, then email
    client: Client | None = None
    if phone:
        client = Client.objects.filter(phone=phone).first()
    if client is None and email:
        client = Client.objects.filter(email=email).first()

    if client is not None:
        return client

    return Client.objects.create(
        first_name=first_name,
        last_name=last_name,
        phone=phone or None,
        email=email or None,
        is_ghost=True,
        status=Client.STATUS_GUEST,
    )


class BookingCommitView(View):
    """POST — validate contact, create appointments, redirect to success page.

    Three commit paths:
      1. Single service  → 1 Appointment, redirect success_single
      2. same_day (2+)  → AppointmentGroup + items, redirect success_group
      3. multi_day      → N independent Appointments, redirect success_multi
    """

    def post(self, request: HttpRequest) -> HttpResponse:
        cart = get_cart(request)

        # Validate cart readiness
        if cart.is_empty():
            return self._error(request, cart, _("bk_err_empty_cart"))

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        notes = request.POST.get("client_notes", "").strip()

        request_call = request.POST.get("request_call") == "on"
        cancellation_policy = request.POST.get("cancellation_policy") == "on"
        consent = request.POST.get("consent") == "on"

        # Persist contact and choices in session early (to preserve data on validation errors)
        cart.contact = {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "email": email,
            "notes": notes,
            "request_call": request_call,
            "cancellation_policy": cancellation_policy,
            "consent": consent,
        }
        save_cart(request, cart)

        if not first_name or not last_name:
            return self._error(request, cart, _("bk_err_name_required"))
        if not phone and not email:
            return self._error(request, cart, _("bk_err_contact_required"))

        if not cancellation_policy:
            messages.error(request, _("bk_err_cancellation_required"))
            return self._error(request, cart, "")
        if not consent:
            messages.error(request, _("bk_err_consent_required"))
            return self._error(request, cart, "")

        # Validate slot selection
        if cart.mode == "same_day":
            if not cart.is_ready_same_day():
                return self._error(request, cart, _("bk_err_time_required"))
        else:
            if not cart.is_ready_multi_day():
                return self._error(request, cart, _("bk_err_multi_time_required"))

        try:
            with transaction.atomic():
                client = _get_or_create_client(first_name, last_name, phone, email)

                if cart.mode == "same_day":
                    redirect_url = self._commit_same_day(request, cart, client)
                else:
                    redirect_url = self._commit_multi_day(request, cart, client)

            clear_cart(request)
            response = HttpResponse(status=200)
            response["HX-Redirect"] = redirect_url
            return response

        except Exception as exc:
            logger.exception("BookingCommitView: Commit failed")
            return self._error(request, cart, _("bk_err_commit_failed") % {"exc": str(exc)})

    # ------------------------------------------------------------------

    def _commit_same_day(self, request: HttpRequest, cart, client: Client) -> str:
        """Commit same-day booking. Returns success URL."""
        gateway = get_booking_engine_gateway()
        target_date = datetime.date.fromisoformat(cart.date)

        result = gateway.create_booking(
            service_ids=cart.service_ids(),
            target_date=target_date,
            selected_time=cart.time,
            resource_id=None,
            client=client,
            notify_received=False,
            extra_fields={"client_notes": cart.contact.get("notes", "")} if cart.contact.get("notes") else None,
        )

        appointments = result if isinstance(result, list) else [result]

        notes = cart.contact.get("notes", "")
        if notes and appointments:
            from features.conversations.services.threads import create_booking_thread

            create_booking_thread(appointments[0])

        from features.conversations.services.notifications import _get_engine

        engine = _get_engine()

        if len(appointments) == 1:
            # Single appointment — no group
            appt = appointments[0]
            self._apply_combo_pricing(cart, appointments)
            engine.dispatch_event("booking.received", appt)
            return reverse("booking:success_single", kwargs={"token": appt.finalize_token})

        # 2+ appointments → create group
        group = AppointmentGroup.objects.create(
            client=client,
            mode="same_day",
            source="website",
            combo_id=cart.combo_id,
        )
        self._apply_combo_pricing(cart, appointments)
        for order, appt in enumerate(appointments):
            AppointmentGroupItem.objects.create(
                group=group,
                appointment=appt,
                order=order,
            )

        engine.dispatch_event("booking.group_received", group)
        return reverse("booking:success_group", kwargs={"token": group.group_token})

    def _apply_combo_pricing(self, cart, appointments: list) -> None:
        if not cart.combo_id or cart.combo_price is None or not appointments:
            return

        combo = ServiceCombo.objects.filter(pk=cart.combo_id, discount_type=ServiceCombo.FIXED_PRICE).first()
        if combo is None:
            return

        target_total = Decimal(cart.combo_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        base_total = sum((appt.price for appt in appointments), Decimal("0"))
        remaining = target_total

        for index, appt in enumerate(appointments):
            if index == len(appointments) - 1:
                price_actual = remaining
            elif base_total > 0:
                price_actual = (target_total * (appt.price / base_total)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                remaining -= price_actual
            else:
                price_actual = (target_total / len(appointments)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                remaining -= price_actual

            appt.price_actual = price_actual
            appt.save(update_fields=["price_actual", "updated_at"])

    def _commit_multi_day(self, request: HttpRequest, cart, client: Client) -> str:
        """Commit multi-day booking — independent appointments, no group."""
        gateway = get_booking_engine_gateway()
        tokens: list[str] = []

        for item in cart.items:
            target_date = datetime.date.fromisoformat(item.date)
            result = gateway.create_booking(
                service_ids=[item.service_id],
                target_date=target_date,
                selected_time=item.time,
                resource_id=None,
                client=client,
                extra_fields={"client_notes": cart.contact.get("notes", "")} if cart.contact.get("notes") else None,
            )
            appts = result if isinstance(result, list) else [result]
            for appt in appts:
                tokens.append(appt.finalize_token)

        notes = cart.contact.get("notes", "")
        if notes and tokens:
            from features.booking.models import Appointment
            from features.conversations.services.threads import create_booking_thread

            first_appt = Appointment.objects.filter(finalize_token=tokens[0]).first()
            if first_appt:
                create_booking_thread(first_appt)

        tokens_param = ",".join(tokens)
        return f"{reverse('booking:success_multi')}?tokens={tokens_param}"

    def _error(self, request: HttpRequest, cart, message: str) -> HttpResponse:
        return render(
            request,
            "features/booking/partials/summary_panel.html",
            {"cart": cart, "error": message},
        )


class BookingSuccessSingleView(View):
    """Success page for single appointment booking."""

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        from features.booking.models import Appointment

        appt = get_object_or_404(Appointment, finalize_token=token)
        return render(
            request,
            "features/booking/success_single.html",
            {"appointment": appt},
        )


class BookingSuccessGroupView(View):
    """Success page for same-day group booking."""

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        group = get_object_or_404(
            AppointmentGroup.objects.prefetch_related("items__appointment__service"),
            group_token=token,
        )
        return render(
            request,
            "features/booking/success_group.html",
            {"group": group},
        )


class BookingSuccessMultiView(View):
    """Success page for multi-day independent appointments."""

    def get(self, request: HttpRequest) -> HttpResponse:
        from features.booking.models import Appointment

        raw_tokens = request.GET.get("tokens", "")
        tokens = [t.strip() for t in raw_tokens.split(",") if t.strip()]
        appointments = list(
            Appointment.objects.filter(finalize_token__in=tokens).select_related("service").order_by("datetime_start")
        )
        return render(
            request,
            "features/booking/success_multi.html",
            {"appointments": appointments},
        )
