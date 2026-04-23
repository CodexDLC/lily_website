"""Project provider for resource-slot booking — real ORM implementation."""

from __future__ import annotations

import datetime as dt_module
from typing import Any

from codex_django.booking import (
    BookingActionResult,
    BookingCalendarPrefillState,
    BookingFeatureModels,
    BookingProjectDataProvider,
    BookingQuickCreateClientOptionState,
    BookingQuickCreateServiceOptionState,
)
from core.logger import logger
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from system.models import Client

from features.main.models import Service, ServiceCategory

from ..booking_settings import BookingSettings
from ..models import Appointment, Master, MasterDayOff, MasterWorkingDay


class RuntimeBookingProvider(BookingProjectDataProvider):
    """Project provider backed by real Django ORM."""

    BLOCKING_APPOINTMENT_STATUSES = (
        Appointment.STATUS_PENDING,
        Appointment.STATUS_CONFIRMED,
        Appointment.STATUS_RESCHEDULE_PROPOSED,
    )

    @staticmethod
    def get_bookable_masters_queryset():
        return (
            Master.objects.filter(status=Master.STATUS_ACTIVE)
            .annotate(working_days_count=Count("working_days", distinct=True))
            .filter(working_days_count__gt=0)
        )

    @classmethod
    def get_bookable_services_queryset(cls):
        return (
            Service.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("masters")
            .annotate(
                bookable_masters_count=Count(
                    "masters",
                    filter=Q(masters__status=Master.STATUS_ACTIVE, masters__working_days__isnull=False),
                    distinct=True,
                )
            )
            .filter(bookable_masters_count__gt=0)
            .order_by("category__order", "order")
        )

    @classmethod
    def get_cabinet_bookable_services_queryset(cls):
        return cls.get_bookable_services_queryset().filter(category__is_active=True, category__is_planned=False)

    # ── Feature models contract ───────────────────────────────────────────────

    def get_feature_models(self) -> BookingFeatureModels:
        return BookingFeatureModels(
            appointment_model=Appointment,
            resource_model=Master,
            service_model=Service,
            working_day_model=MasterWorkingDay,
            day_off_model=MasterDayOff,
            booking_settings_model=BookingSettings,
        )

    # ── Category / Service lists ──────────────────────────────────────────────

    def get_service_categories(self) -> Any:
        category_ids = self.get_cabinet_bookable_services_queryset().values_list("category_id", flat=True)
        return ServiceCategory.objects.prefetch_related(
            Prefetch("services", queryset=self.get_cabinet_bookable_services_queryset())
        ).filter(is_active=True, is_planned=False, id__in=category_ids)

    def get_public_services(self) -> list[dict[str, Any]]:
        """Services for the public booking page — includes conflict rule data."""
        from features.main.models import ServiceConflictRule

        # Build a mapping: service_id → list of conflict rules
        rules_from: dict[int, list[dict]] = {}
        for rule in ServiceConflictRule.objects.filter(is_active=True).select_related("target"):
            rules_from.setdefault(rule.source_id, []).append({"target_id": rule.target_id, "rule_type": rule.rule_type})

        result = []
        for s in self.get_bookable_services_queryset():
            result.append(
                {
                    "id": s.id,
                    "title": s.name,
                    "slug": s.slug,
                    "price": str(s.price),
                    "duration": s.duration,
                    "category_id": s.category_id,
                    "category_slug": s.category.slug,
                    "category_name": s.category.name,
                    "is_addon": s.is_addon,
                    "is_hit": s.is_hit,
                    "conflict_rules": rules_from.get(s.id, []),
                }
            )
        return result

    def get_cabinet_services(self) -> list[dict[str, Any]]:
        from features.main.models import ServiceConflictRule

        # Build a mapping: service_id → list of conflict rules
        rules_from: dict[int, list[dict]] = {}
        for rule in ServiceConflictRule.objects.filter(is_active=True):
            rules_from.setdefault(rule.source_id, []).append({"target_id": rule.target_id, "rule_type": rule.rule_type})

        return [
            {
                "id": s.id,
                "title": s.name,
                "price": float(s.price),
                "duration": s.duration,
                "category": s.category.bento_group or s.category.slug,
                "master_ids": list(s.masters.values_list("id", flat=True)),
                "conflicts_with": [r["target_id"] for r in rules_from.get(s.id, [])],
                "conflict_rules": rules_from.get(s.id, []),
            }
            for s in self.get_cabinet_bookable_services_queryset()
        ]

    # ── Master list ───────────────────────────────────────────────────────────

    def get_cabinet_masters(self) -> list[dict[str, Any]]:
        return [{"id": m.id, "name": m.name} for m in self.get_bookable_masters_queryset().order_by("order", "name")]

    # ── Client list ───────────────────────────────────────────────────────────

    def get_cabinet_clients(self) -> list[dict[str, Any]]:
        return [
            {
                "id": c.id,
                "name": c.full_name or c.phone or c.email or str(c),
                "phone": c.phone or "",
                "email": c.email or "",
            }
            for c in Client.objects.exclude(status=Client.STATUS_BLOCKED).order_by("last_name", "first_name")
        ]

    # ── Appointment list ──────────────────────────────────────────────────────

    def get_cabinet_appointments(self, **kwargs: Any) -> list[dict[str, Any]]:
        status = kwargs.get("status")
        master_id = kwargs.get("master_id")
        search = kwargs.get("search")
        date_from = kwargs.get("date_from")
        date_to = kwargs.get("date_to")

        qs = Appointment.objects.select_related("master", "service", "client")

        if status and status != "all":
            qs = qs.filter(status=status)
        if master_id:
            qs = qs.filter(master_id=master_id)
        if search:
            qs = qs.filter(
                Q(client__first_name__icontains=search)
                | Q(client__last_name__icontains=search)
                | Q(client__phone__icontains=search)
                | Q(service__name__icontains=search)
            )
        if date_from:
            qs = qs.filter(datetime_start__date__gte=date_from)
        if date_to:
            qs = qs.filter(datetime_start__date__lte=date_to)

        result = []
        qs = qs.order_by("-datetime_start")
        for appt in qs:
            local_dt = timezone.localtime(appt.datetime_start)
            client = appt.client
            client_name = getattr(client, "full_name", str(client)) if client else str(_("Unnamed Client"))
            price = appt.price_actual if appt.price_actual is not None else appt.price

            result.append(
                {
                    "id": appt.id,
                    "master_id": appt.master_id,
                    "date": local_dt.strftime("%Y-%m-%d"),
                    "time": local_dt.strftime("%H:%M"),
                    "duration": appt.duration_minutes,
                    "client_name": client_name,
                    "admin_notes": appt.admin_notes,
                    "client_notes": appt.client_notes,
                    "client_created_at": client.created_at.isoformat() if client else None,
                    "phone": client.phone if client else "",
                    "service_title": appt.service.name,
                    "price": float(price),
                    "status": appt.status,
                }
            )
        return result

    # ── Schedule prefill (click on calendar slot) ─────────────────────────────

    def get_schedule_prefill(self, *, schedule_date: str, col: int, row: int) -> BookingCalendarPrefillState:
        masters = list(self.get_bookable_masters_queryset().order_by("order", "name"))
        master = masters[col] if 0 <= col < len(masters) else None
        return BookingCalendarPrefillState(
            resource_id=master.id if master else None,
            resource_name=master.name if master else "Any specialist",
            booking_date=schedule_date,
            start_time=self._row_to_time(row),
            slot_duration_minutes=30,
            col=col,
            row=row,
        )

    @staticmethod
    def _row_to_time(row: int) -> str:
        """Convert calendar row index (30-min slots from 08:00) to HH:MM string."""
        total_minutes = 8 * 60 + row * 30
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

    # ── Quick-create: services dropdown ──────────────────────────────────────

    def get_quick_create_services(
        self,
        *,
        resource_id: int | None,
        booking_date: str,
        start_time: str,
    ) -> list[BookingQuickCreateServiceOptionState]:
        del booking_date, start_time
        qs = self.get_cabinet_bookable_services_queryset()
        if resource_id:
            qs = qs.filter(masters__id=resource_id)
        return [
            BookingQuickCreateServiceOptionState(
                value=str(s.id),
                label=s.name,
                price_label=f"€{s.price}",
                duration_label=f"{s.duration} min",
            )
            for s in qs
        ]

    # ── Quick-create: client dropdown ─────────────────────────────────────────

    def get_quick_create_clients(self) -> list[BookingQuickCreateClientOptionState]:
        return [
            BookingQuickCreateClientOptionState(
                value=str(c.id),
                label=c.full_name or c.phone or c.email or str(c),
                subtitle=c.phone or c.email or "",
                email=c.email or "",
                search_text=" ".join(part.lower() for part in [c.full_name, c.phone or "", c.email or ""] if part),
            )
            for c in Client.objects.exclude(status=Client.STATUS_BLOCKED).order_by("last_name", "first_name")
        ]

    # ── Quick-create: available time slots ────────────────────────────────────

    def get_quick_create_slot_options(
        self,
        *,
        resource_id: int,
        booking_date: str,
        service_ids: list[int] | None = None,
    ) -> list[str]:
        """Return available slot times via real availability engine.

        If service_ids are provided, uses the library's smart slot calculator (ChainFinder).
        Otherwise, uses the engine's free windows partitioned by the grid step.
        """
        from features.booking.selector.engine import get_booking_engine_gateway

        try:
            target_date = dt_module.date.fromisoformat(booking_date)
        except ValueError:
            return []

        gateway = get_booking_engine_gateway()

        # If we have services, use the library's smart search
        if service_ids:
            try:
                result = gateway.get_available_slots(
                    service_ids=service_ids,
                    target_date=target_date,
                    locked_resource_id=resource_id,
                    audience="cabinet",
                )
                return result.get_unique_start_times()
            except Exception:
                # Fallback to grid if smart search fails
                logger.debug("Smart search failed, falling back to grid calculation")

        try:
            return gateway.get_resource_day_slots(resource_id=resource_id, target_date=target_date, audience="cabinet")
        except Exception:
            return []

    # ── Quick-create: create client ───────────────────────────────────────────

    def create_quick_client(
        self,
        *,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
    ) -> dict[str, object]:
        """Find existing Client by phone/email, or create a new ghost Client."""
        client = None
        if phone:
            client = Client.objects.filter(phone=phone).first()
        if not client and email:
            client = Client.objects.filter(email=email).first()

        if not client:
            client = Client.objects.create(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                phone=phone or None,
                email=email or None,
                is_ghost=True,
                status=Client.STATUS_GUEST,
            )

        return {
            "id": client.id,
            "name": client.full_name or client.phone or client.email or str(client),
            "phone": client.phone or "",
            "email": client.email or "",
        }

    # ── Quick-create: create appointment ─────────────────────────────────────

    def create_quick_appointment(
        self,
        *,
        resource_id: int,
        booking_date: str,
        start_time: str,
        service_id: int,
        client_name: str,
        client_phone: str,
        client_email: str = "",
    ) -> dict[str, object]:
        try:
            service = Service.objects.get(id=service_id)
            master = Master.objects.get(id=resource_id)
            naive_dt = dt_module.datetime.strptime(f"{booking_date} {start_time}", "%Y-%m-%d %H:%M")
        except (Service.DoesNotExist, Master.DoesNotExist):
            return {"id": 0, "error": "Service or master not found"}
        except ValueError:
            return {"id": 0, "error": "Invalid booking date or time"}

        aware_dt = timezone.make_aware(naive_dt)
        if self._has_blocking_overlap(
            resource_id=master.id,
            start_at=aware_dt,
            duration_minutes=service.duration,
        ):
            return {
                "id": 0,
                "error": "Selected slot is already occupied. Choose another time.",
                "code": "slot-overlap",
            }

        client: Client | None = None
        if client_phone:
            client = Client.objects.filter(phone=client_phone).first()
        if not client and client_email:
            client = Client.objects.filter(email=client_email).first()
        if not client:
            name_parts = client_name.strip().split(" ", 1)
            client = Client.objects.create(
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else "",
                phone=client_phone or None,
                email=client_email or None,
                is_ghost=True,
                status=Client.STATUS_GUEST,
            )

        with transaction.atomic():
            if self._has_blocking_overlap(
                resource_id=master.id,
                start_at=aware_dt,
                duration_minutes=service.duration,
            ):
                return {
                    "id": 0,
                    "error": "Selected slot is already occupied. Choose another time.",
                    "code": "slot-overlap",
                }
            appt = Appointment.objects.create(
                client=client,
                master=master,
                service=service,
                datetime_start=aware_dt,
                duration_minutes=service.duration,
                price=service.price,
                source=Appointment.SOURCE_ADMIN,
            )
        return {
            "id": appt.id,
            "master_id": appt.master_id,
            "date": booking_date,
            "time": start_time,
            "duration": appt.duration_minutes,
            "client_name": client_name,
            "phone": client_phone,
            "service_title": service.name,
            "price": float(appt.price),
            "status": appt.status,
        }

    # ── Update appointment datetime ───────────────────────────────────────────

    def update_quick_appointment(
        self, *, booking_id: int, booking_date: str, start_time: str
    ) -> dict[str, object] | None:
        try:
            appt = Appointment.objects.get(id=booking_id)
        except Appointment.DoesNotExist:
            return None

        naive_dt = dt_module.datetime.strptime(f"{booking_date} {start_time}", "%Y-%m-%d %H:%M")
        aware_dt = timezone.make_aware(naive_dt)
        if self._has_blocking_overlap(
            resource_id=appt.master_id,
            start_at=aware_dt,
            duration_minutes=appt.duration_minutes,
            exclude_appointment_id=appt.id,
        ):
            return {"id": 0, "error": "Selected slot is already occupied. Choose another time.", "code": "slot-overlap"}
        appt.datetime_start = aware_dt
        appt.save(update_fields=["datetime_start", "updated_at"])
        return {"id": appt.id, "date": booking_date, "time": start_time}

    def _has_blocking_overlap(
        self,
        *,
        resource_id: int,
        start_at: dt_module.datetime,
        duration_minutes: int,
        exclude_appointment_id: int | None = None,
    ) -> bool:
        end_at = start_at + dt_module.timedelta(minutes=duration_minutes)
        day_start = start_at.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + dt_module.timedelta(days=1)
        qs = Appointment.objects.filter(
            master_id=resource_id,
            datetime_start__gte=day_start,
            datetime_start__lt=day_end,
            status__in=self.BLOCKING_APPOINTMENT_STATUSES,
        )
        if exclude_appointment_id:
            qs = qs.exclude(pk=exclude_appointment_id)
        return any(
            appt.datetime_start < end_at
            and appt.datetime_start + dt_module.timedelta(minutes=appt.duration_minutes) > start_at
            for appt in qs.only("datetime_start", "duration_minutes")
        )

    # ── Cabinet action (confirm / cancel / reschedule) ────────────────────────

    def run_cabinet_action(
        self,
        *,
        booking_id: int,
        action: str,
        redirect_url: str = "",
        **kwargs: Any,
    ) -> BookingActionResult:
        """Execute a booking action using model business rules."""
        payload = kwargs.get("payload", {})
        try:
            appt = Appointment.objects.get(pk=booking_id)
        except Appointment.DoesNotExist:
            return BookingActionResult(
                ok=False,
                code="booking-not-found",
                message="Appointment not found.",
                ui_effect="none",
                target_url="",
            )

        if action == "confirm":
            from django.core.exceptions import ValidationError

            try:
                appt.confirm()
                # 6.4: Send confirmation notification
                from features.conversations.services.notifications import _get_engine

                _get_engine().dispatch_event("booking.confirmed", appt)

                return BookingActionResult(
                    ok=True,
                    code="booking-confirm",
                    message=_("Confirmed"),
                    ui_effect="reload_modal",
                    target_url="",
                )
            except ValidationError as e:
                return BookingActionResult(
                    ok=False,
                    code="booking-validation-error",
                    message=str(e),
                    ui_effect="none",
                    target_url="",
                )

        if action == "cancel":
            from django.core.exceptions import ValidationError

            reason = payload.get("cancel_reason", Appointment.CANCEL_REASON_OTHER)
            note = payload.get("cancel_note", "")
            try:
                appt.cancel(reason=reason, note=note)
                # 6.4: Send cancellation notification
                from features.conversations.services.notifications import _get_engine

                _get_engine().dispatch_event("booking.cancelled", appt)

                return BookingActionResult(
                    ok=True,
                    code="booking-cancel",
                    message=_("Cancelled"),
                    ui_effect="reload_modal",
                    target_url="",
                )
            except ValidationError as e:
                return BookingActionResult(
                    ok=False,
                    code="booking-validation-error",
                    message=str(e),
                    ui_effect="none",
                    target_url="",
                )

        if action == "complete":
            from django.core.exceptions import ValidationError

            try:
                appt.mark_completed()
                return BookingActionResult(
                    ok=True,
                    code="booking-complete",
                    message=_("Completed"),
                    ui_effect="reload_modal",
                    target_url="",
                )
            except ValidationError as e:
                return BookingActionResult(
                    ok=False,
                    code="booking-validation-error",
                    message=str(e),
                    ui_effect="none",
                    target_url="",
                )

        if action == "no_show":
            from django.core.exceptions import ValidationError

            try:
                appt.mark_no_show()
                return BookingActionResult(
                    ok=True,
                    code="booking-no-show",
                    message=_("Marked as no show"),
                    ui_effect="reload_modal",
                    target_url="",
                )
            except ValidationError as e:
                return BookingActionResult(
                    ok=False,
                    code="booking-validation-error",
                    message=str(e),
                    ui_effect="none",
                    target_url="",
                )

        if action == "reschedule":
            new_dt_str = payload.get("datetime_start")
            if new_dt_str:
                import datetime as dt_module

                from django.utils import timezone

                # Assuming format %d.%m.%Y %H:%M as per Bot API example
                try:
                    naive_dt = dt_module.datetime.strptime(new_dt_str, "%d.%m.%Y %H:%M")
                    appt.datetime_start = timezone.make_aware(naive_dt)
                    appt.save(update_fields=["datetime_start", "updated_at"])
                    return BookingActionResult(
                        ok=True,
                        code="booking-reschedule",
                        message=_("Rescheduled"),
                        ui_effect="reload_modal",
                        target_url="",
                    )
                except (ValueError, TypeError):
                    return BookingActionResult(
                        ok=False,
                        code="booking-invalid-format",
                        message=_("Invalid datetime format. Use DD.MM.YYYY HH:MM"),
                        ui_effect="none",
                        target_url="",
                    )

        return BookingActionResult(
            ok=False,
            code="booking-unknown",
            message=f"Unknown action: {action}",
            ui_effect="none",
            target_url="",
        )


_provider = RuntimeBookingProvider()


def get_booking_project_data_provider() -> RuntimeBookingProvider:
    """Return the active project provider for the booking scaffold."""
    return _provider
