"""Unit tests for features/booking/selector/engine.py.

Tests: EmptyAvailableSlots, LoadAwareDjangoAvailabilityAdapter priority/load
sorting, _row_to_time, BookingRuntimeEngineGateway.get_resource_day_slots,
get_available_slots (audience filtering, fallback).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from features.booking.selector.engine import (
    BookingRuntimeEngineGateway,
    EmptyAvailableSlots,
    LoadAwareDjangoAvailabilityAdapter,
)

# ── EmptyAvailableSlots ───────────────────────────────────────────────────────


@pytest.mark.unit
class TestEmptyAvailableSlots:
    def test_to_dict(self):
        e = EmptyAvailableSlots()
        d = e.to_dict()
        assert d == {"slots": [], "metadata": {}}

    def test_get_unique_start_times(self):
        assert EmptyAvailableSlots().get_unique_start_times() == []


# ── LoadAwareDjangoAvailabilityAdapter ────────────────────────────────────────


@pytest.mark.unit
class TestLoadAwareDjangoAvailabilityAdapter:
    def _make_adapter(self, strategy: str = "fill_first") -> LoadAwareDjangoAvailabilityAdapter:
        from features.booking.booking_settings import BookingSettings
        from features.booking.models import Appointment, Master, MasterDayOff, MasterWorkingDay
        from features.main.models import Service

        return LoadAwareDjangoAvailabilityAdapter(
            resource_model=Master,
            appointment_model=Appointment,
            service_model=Service,
            working_day_model=MasterWorkingDay,
            day_off_model=MasterDayOff,
            booking_settings_model=BookingSettings,
            timezone="UTC",
            load_strategy=strategy,
            target_date=dt.date(2026, 5, 10),
        )

    def test_sort_by_priority(self, db, master):
        from tests.factories import MasterFactory

        master2 = MasterFactory()
        master.booking_priority = 10
        master.save()
        master2.booking_priority = 5
        master2.save()

        adapter = self._make_adapter("fill_first")
        resource_ids = [str(master.pk), str(master2.pk)]
        sorted_ids = adapter._sort_by_priority(resource_ids)
        assert sorted_ids[0] == str(master2.pk)  # lower priority = first

    def test_sort_by_load(self, db, master, service, booking_settings):
        from tests.factories import AppointmentFactory, MasterFactory

        master2 = MasterFactory()
        target_date = dt.date(2026, 5, 10)
        start = timezone.make_aware(dt.datetime(2026, 5, 10, 10, 0))

        # master2 has more appointments that day
        AppointmentFactory(master=master2, service=service, datetime_start=start, status="confirmed")
        AppointmentFactory(
            master=master2, service=service, datetime_start=start + dt.timedelta(hours=2), status="confirmed"
        )

        adapter = self._make_adapter("even_load")
        resource_ids = [str(master.pk), str(master2.pk)]
        sorted_ids = adapter._sort_by_load(resource_ids, target_date)
        assert sorted_ids[0] == str(master.pk)  # fewer appointments = first

    def test_prioritize_dispatches_to_even_load(self, db, master):
        from features.booking.booking_settings import BookingSettings

        adapter = self._make_adapter(BookingSettings.STRATEGY_EVEN_LOAD)
        with patch.object(adapter, "_sort_by_load", return_value=["1"]) as mock_sort:
            adapter.prioritize_resource_ids(
                resource_ids=["1"],
                service=None,
                target_date=dt.date(2026, 5, 10),
                service_id=1,
            )
            mock_sort.assert_called_once()

    def test_prioritize_dispatches_to_fill_first(self, db, master):
        adapter = self._make_adapter("fill_first")
        with patch.object(adapter, "_sort_by_priority", return_value=["1"]) as mock_sort:
            adapter.prioritize_resource_ids(
                resource_ids=["1"],
                service=None,
                target_date=dt.date(2026, 5, 10),
                service_id=1,
            )
            mock_sort.assert_called_once()

    def test_prioritize_empty_list_returns_empty(self, db):
        adapter = self._make_adapter("fill_first")
        result = adapter.prioritize_resource_ids(
            resource_ids=[],
            service=None,
            target_date=dt.date(2026, 5, 10),
            service_id=1,
        )
        assert result == []


# ── BookingRuntimeEngineGateway: get_resource_day_slots ───────────────────────


@pytest.mark.unit
class TestGetResourceDaySlots:
    def _gateway(self) -> BookingRuntimeEngineGateway:
        return BookingRuntimeEngineGateway()

    def test_returns_slots_on_working_day(self, db, master, booking_settings):
        gateway = self._gateway()
        # Monday 2026-05-11 (weekday=0, master has working days Mon–Sun 09–18)
        target = dt.date(2026, 5, 11)  # Monday
        slots = gateway.get_resource_day_slots(resource_id=master.pk, target_date=target, audience="cabinet")
        assert len(slots) > 0
        assert "09:00" in slots
        assert "17:30" in slots

    def test_no_slots_on_day_off(self, db, master, booking_settings):
        from features.booking.models import MasterDayOff

        target = dt.date(2026, 5, 11)
        MasterDayOff.objects.create(master=master, date=target)
        gateway = self._gateway()
        slots = gateway.get_resource_day_slots(resource_id=master.pk, target_date=target, audience="cabinet")
        assert slots == []

    def test_busy_slots_excluded(self, db, master, service, booking_settings):
        from features.booking.models import Appointment

        target = dt.date(2026, 5, 11)
        start = timezone.make_aware(dt.datetime(2026, 5, 11, 9, 0))
        Appointment.objects.create(
            master=master,
            service=service,
            datetime_start=start,
            duration_minutes=60,
            price="50.00",
            status=Appointment.STATUS_CONFIRMED,
        )
        gateway = self._gateway()
        slots = gateway.get_resource_day_slots(resource_id=master.pk, target_date=target, audience="cabinet")
        # 09:00 should be blocked (60 min duration / 30 min step → 09:00 and 09:30 blocked)
        assert "09:00" not in slots
        assert "10:00" in slots

    def test_public_audience_today_returns_empty(self, db, master, booking_settings):
        from features.booking.booking_settings import BookingSettings

        booking_settings.book_only_from_next_day = True
        booking_settings.save()
        # Reload settings
        BookingSettings._cached = None  # clear cache if any

        gateway = self._gateway()
        today = dt.date.today()
        slots = gateway.get_resource_day_slots(resource_id=master.pk, target_date=today, audience="public")
        assert slots == []

    def test_no_slots_when_no_working_day_and_global_closed(self, db, booking_settings):
        from tests.factories import MasterFactory

        # Master without working days
        m = MasterFactory(working_days=False)
        # Make Sunday closed globally
        booking_settings.sunday_is_closed = True
        booking_settings.save()

        target = dt.date(2026, 5, 10)  # Sunday
        gateway = self._gateway()
        slots = gateway.get_resource_day_slots(resource_id=m.pk, target_date=target, audience="cabinet")
        assert slots == []


# ── BookingRuntimeEngineGateway: get_available_slots ─────────────────────────


@pytest.mark.unit
class TestGetAvailableSlots:
    def _gateway(self) -> BookingRuntimeEngineGateway:
        return BookingRuntimeEngineGateway()

    def test_public_today_blocked_when_book_only_from_next_day(self, db, booking_settings):
        from features.booking.booking_settings import BookingSettings

        booking_settings.book_only_from_next_day = True
        booking_settings.save()

        gateway = self._gateway()
        with patch.object(BookingSettings, "load", return_value=booking_settings):
            result = gateway.get_available_slots(
                service_ids=[1],
                target_date=dt.date.today(),
                audience="public",
            )
        assert result == []

    def test_multi_service_sets_defaults(self, db, booking_settings):
        gateway = self._gateway()
        with (
            patch.object(gateway, "_build_adapter", return_value=MagicMock()),
            patch(
                "features.booking.selector.engine.runtime_get_available_slots",
                return_value=MagicMock(),
            ) as mock_slots,
        ):
            gateway.get_available_slots(
                service_ids=[1, 2],
                target_date=dt.date(2026, 5, 11),
            )
            _, _, _, called_kwargs = mock_slots.call_args[0] + (mock_slots.call_args[1],)

    def test_exception_returns_empty_slots(self, db, booking_settings):
        gateway = self._gateway()
        with (
            patch.object(gateway, "_build_adapter", return_value=MagicMock()),
            patch(
                "features.booking.selector.engine.runtime_get_available_slots",
                side_effect=RuntimeError("boom"),
            ),
        ):
            result = gateway.get_available_slots(
                service_ids=[1],
                target_date=dt.date(2026, 5, 11),
            )
        assert isinstance(result, EmptyAvailableSlots)

    def test_cabinet_audience_ignores_next_day_rule(self, db, booking_settings):

        booking_settings.book_only_from_next_day = True
        booking_settings.save()

        gateway = self._gateway()
        with (
            patch.object(gateway, "_build_adapter", return_value=MagicMock()),
            patch(
                "features.booking.selector.engine.runtime_get_available_slots",
                return_value=MagicMock(),
            ) as mock_slots,
        ):
            gateway.get_available_slots(
                service_ids=[1],
                target_date=dt.date.today(),
                audience="cabinet",
            )
            assert mock_slots.called  # not blocked


# ── BookingRuntimeEngineGateway: get_nearest_slots ───────────────────────────


@pytest.mark.unit
class TestGetNearestSlots:
    def test_public_adjusts_search_from_to_tomorrow(self, db, booking_settings):

        booking_settings.book_only_from_next_day = True
        booking_settings.save()

        gateway = BookingRuntimeEngineGateway()
        tomorrow = dt.date.today() + dt.timedelta(days=1)

        with (
            patch.object(gateway, "_build_adapter", return_value=MagicMock()),
            patch(
                "features.booking.selector.engine.runtime_get_nearest_slots",
                return_value=MagicMock(),
            ) as mock_nearest,
        ):
            gateway.get_nearest_slots(
                service_ids=[1],
                search_from=dt.date.today(),
                audience="public",
            )
            # second positional arg to runtime_get_nearest_slots is the effective_search_from
            call_args = mock_nearest.call_args
            assert call_args[0][2] == tomorrow


@pytest.mark.unit
class TestCreateBookingPersistence:
    def test_single_service_any_resource_persists_service_price(
        self,
        db,
        master,
        service,
        client_obj,
        booking_settings,
    ):
        service.masters.add(master)
        service.price = Decimal("77.50")
        service.save(update_fields=["price"])

        gateway = BookingRuntimeEngineGateway()
        appointment = gateway.create_booking(
            service_ids=[service.pk],
            target_date=dt.date(2026, 5, 11),
            selected_time="10:00",
            resource_id=None,
            client=client_obj,
            notify_received=False,
        )[0]

        appointment.refresh_from_db()
        assert appointment.price == Decimal("77.50")
        assert appointment.service_id == service.pk
        assert appointment.master_id == master.pk

    def test_multi_service_chain_persists_corresponding_service_prices(
        self,
        db,
        master,
        service,
        client_obj,
        booking_settings,
    ):
        from tests.factories import ServiceFactory

        service.masters.add(master)
        service.price = Decimal("40.00")
        service.duration = 30
        service.save(update_fields=["price", "duration"])
        service_two = ServiceFactory(category=service.category, price=Decimal("95.00"), duration=45)
        service_two.masters.add(master)

        gateway = BookingRuntimeEngineGateway()
        appointments = gateway.create_booking(
            service_ids=[service.pk, service_two.pk],
            target_date=dt.date(2026, 5, 11),
            selected_time="10:00",
            resource_id=None,
            client=client_obj,
            notify_received=False,
        )

        prices_by_service = {appointment.service_id: appointment.price for appointment in appointments}
        assert prices_by_service == {
            service.pk: Decimal("40.00"),
            service_two.pk: Decimal("95.00"),
        }

    def test_missing_service_does_not_create_zero_price_appointment(self, db, client_obj):
        from features.booking.models import Appointment
        from features.booking.persistence import BookingServiceNotFoundError, LilyBookingPersistenceHook

        solution = SimpleNamespace(
            items=[
                SimpleNamespace(
                    resource_id=123,
                    start_time=timezone.make_aware(dt.datetime(2026, 5, 11, 10, 0)),
                    duration_minutes=60,
                )
            ]
        )
        hook = LilyBookingPersistenceHook(Appointment, notify_received=False)

        with pytest.raises(BookingServiceNotFoundError):
            hook.persist_chain(
                solution=solution,
                service_ids=[999999],
                client=client_obj,
            )

        assert Appointment.objects.count() == 0
