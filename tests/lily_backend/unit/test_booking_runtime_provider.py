"""Unit tests for features/booking/providers/runtime.py (RuntimeBookingProvider).

Uses sqlite in-memory via pytest-django; all model fixtures from conftest.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from features.booking.providers.runtime import RuntimeBookingProvider


@pytest.fixture
def provider():
    return RuntimeBookingProvider()


# ── get_bookable_masters_queryset ─────────────────────────────────────────────


@pytest.mark.unit
class TestGetBookableMastersQueryset:
    def test_active_master_with_working_days_is_included(self, db, master):
        qs = RuntimeBookingProvider.get_bookable_masters_queryset()
        assert qs.filter(pk=master.pk).exists()

    def test_inactive_master_excluded(self, db):
        from tests.factories import MasterFactory

        inactive = MasterFactory(status="inactive")
        qs = RuntimeBookingProvider.get_bookable_masters_queryset()
        assert not qs.filter(pk=inactive.pk).exists()

    def test_master_without_working_days_excluded(self, db):
        from tests.factories import MasterFactory

        m = MasterFactory(working_days=False)
        qs = RuntimeBookingProvider.get_bookable_masters_queryset()
        assert not qs.filter(pk=m.pk).exists()


# ── get_bookable_services_queryset ────────────────────────────────────────────


@pytest.mark.unit
class TestGetBookableServicesQueryset:
    def test_active_service_with_active_master_is_included(self, db, master, service):
        master.categories.add(service.category)
        service.masters.add(master)
        qs = RuntimeBookingProvider.get_bookable_services_queryset()
        assert qs.filter(pk=service.pk).exists()

    def test_inactive_service_excluded(self, db, master, service):
        service.is_active = False
        service.save()
        qs = RuntimeBookingProvider.get_bookable_services_queryset()
        assert not qs.filter(pk=service.pk).exists()

    def test_service_with_no_active_masters_excluded(self, db, service):
        qs = RuntimeBookingProvider.get_bookable_services_queryset()
        assert not qs.filter(pk=service.pk).exists()


# ── get_public_services ────────────────────────────────────────────────────────


@pytest.mark.unit
class TestGetPublicServices:
    def test_returns_service_dict_structure(self, db, master, service, provider):
        service.masters.add(master)
        result = provider.get_public_services()
        assert any(s["id"] == service.pk for s in result)
        s = next(s for s in result if s["id"] == service.pk)
        assert "title" in s
        assert "price" in s
        assert "duration" in s
        assert "conflict_rules" in s

    def test_empty_when_no_bookable_services(self, db, provider):
        result = provider.get_public_services()
        assert result == []


# ── get_cabinet_services ──────────────────────────────────────────────────────


@pytest.mark.unit
class TestGetCabinetServices:
    def test_includes_master_ids(self, db, master, service, provider):
        service.masters.add(master)
        result = provider.get_cabinet_services()
        s = next((s for s in result if s["id"] == service.pk), None)
        assert s is not None
        assert master.pk in s["master_ids"]


# ── get_cabinet_masters ───────────────────────────────────────────────────────


@pytest.mark.unit
class TestGetCabinetMasters:
    def test_returns_master_dicts(self, db, master, provider):
        result = provider.get_cabinet_masters()
        assert any(m["id"] == master.pk for m in result)

    def test_inactive_master_not_in_list(self, db, provider):
        from tests.factories import MasterFactory

        inactive = MasterFactory(status="inactive")
        result = provider.get_cabinet_masters()
        assert not any(m["id"] == inactive.pk for m in result)


# ── get_cabinet_clients ───────────────────────────────────────────────────────


@pytest.mark.unit
class TestGetCabinetClients:
    def test_returns_client_dicts(self, db, client_obj, provider):
        result = provider.get_cabinet_clients()
        assert any(c["id"] == client_obj.pk for c in result)

    def test_blocked_client_excluded(self, db, provider):
        from system.models import Client

        blocked = Client.objects.create(
            first_name="Bad",
            phone="+49999888777",
            status=Client.STATUS_BLOCKED,
        )
        result = provider.get_cabinet_clients()
        assert not any(c["id"] == blocked.pk for c in result)


# ── get_cabinet_appointments ──────────────────────────────────────────────────


@pytest.mark.unit
class TestGetCabinetAppointments:
    def test_returns_appointment_dicts(self, db, pending_appointment, provider):
        result = provider.get_cabinet_appointments()
        assert any(a["id"] == pending_appointment.pk for a in result)
        row = next(a for a in result if a["id"] == pending_appointment.pk)
        assert "master_id" in row
        assert "date" in row
        assert "time" in row
        assert "status" in row

    def test_appointment_without_client(self, db, master, service, booking_settings, provider):
        from features.booking.models import Appointment

        appt = Appointment.objects.create(
            client=None,
            master=master,
            service=service,
            datetime_start=timezone.now() + dt.timedelta(hours=48),
            duration_minutes=60,
            price=Decimal("50.00"),
            status=Appointment.STATUS_PENDING,
        )
        result = provider.get_cabinet_appointments()
        assert any(a["id"] == appt.pk for a in result)


# ── get_schedule_prefill ──────────────────────────────────────────────────────


@pytest.mark.unit
class TestGetSchedulePrefill:
    def test_valid_col_returns_master(self, db, master, provider):
        prefill = provider.get_schedule_prefill(schedule_date="2026-05-10", col=0, row=4)
        assert prefill.resource_id == master.pk
        assert prefill.booking_date == "2026-05-10"
        # row 4 → 08:00 + 4*30 = 10:00
        assert prefill.start_time == "10:00"

    def test_col_out_of_bounds_returns_none_resource(self, db, master, provider):
        prefill = provider.get_schedule_prefill(schedule_date="2026-05-10", col=999, row=0)
        assert prefill.resource_id is None

    def test_row_to_time_mapping(self, provider):
        assert provider._row_to_time(0) == "08:00"
        assert provider._row_to_time(2) == "09:00"
        assert provider._row_to_time(20) == "18:00"


# ── get_quick_create_services ─────────────────────────────────────────────────


@pytest.mark.unit
class TestGetQuickCreateServices:
    def test_returns_service_options(self, db, master, service, provider):
        service.masters.add(master)
        result = provider.get_quick_create_services(
            resource_id=master.pk,
            booking_date="2026-05-10",
            start_time="10:00",
        )
        assert any(str(service.pk) == o.value for o in result)

    def test_filters_by_master(self, db, master, service, provider):
        from tests.factories import MasterFactory, ServiceFactory

        other_master = MasterFactory()
        other_service = ServiceFactory()
        other_service.masters.add(other_master)

        result = provider.get_quick_create_services(
            resource_id=master.pk,
            booking_date="2026-05-10",
            start_time="10:00",
        )
        ids = [o.value for o in result]
        assert str(other_service.pk) not in ids

    def test_no_resource_id_returns_all(self, db, master, service, provider):
        service.masters.add(master)
        result = provider.get_quick_create_services(
            resource_id=None,
            booking_date="2026-05-10",
            start_time="10:00",
        )
        assert len(result) >= 1


# ── get_quick_create_clients ──────────────────────────────────────────────────


@pytest.mark.unit
class TestGetQuickCreateClients:
    def test_returns_client_options(self, db, client_obj, provider):
        result = provider.get_quick_create_clients()
        assert any(str(client_obj.pk) == o.value for o in result)

    def test_has_search_text(self, db, client_obj, provider):
        result = provider.get_quick_create_clients()
        opt = next(o for o in result if str(client_obj.pk) == o.value)
        assert opt.search_text  # non-empty string


# ── create_quick_client ───────────────────────────────────────────────────────


@pytest.mark.unit
class TestCreateQuickClient:
    def test_creates_new_client(self, db, provider):
        result = provider.create_quick_client(
            first_name="New",
            last_name="Client",
            phone="+49555444333",
            email="new@test.local",
        )
        assert result["id"] > 0
        assert result["phone"] == "+49555444333"

    def test_finds_existing_by_phone(self, db, client_obj, provider):
        result = provider.create_quick_client(
            first_name="X",
            last_name="Y",
            phone=client_obj.phone,
            email="",
        )
        assert result["id"] == client_obj.pk

    def test_finds_existing_by_email_when_no_phone(self, db, client_obj, provider):
        result = provider.create_quick_client(
            first_name="X",
            last_name="Y",
            phone="",
            email=client_obj.email,
        )
        assert result["id"] == client_obj.pk

    def test_creates_when_both_empty(self, db, provider):
        result = provider.create_quick_client(
            first_name="Ghost",
            last_name="",
            phone="",
            email="",
        )
        assert result["id"] > 0


# ── create_quick_appointment ──────────────────────────────────────────────────


@pytest.mark.unit
class TestCreateQuickAppointment:
    def test_creates_appointment_with_existing_client(self, db, master, service, client_obj, provider):
        result = provider.create_quick_appointment(
            resource_id=master.pk,
            booking_date="2026-05-10",
            start_time="10:00",
            service_id=service.pk,
            client_name=client_obj.full_name,
            client_phone=client_obj.phone,
        )
        assert result["id"] > 0
        assert result["master_id"] == master.pk

    def test_creates_new_client_if_not_found(self, db, master, service, provider):
        result = provider.create_quick_appointment(
            resource_id=master.pk,
            booking_date="2026-05-10",
            start_time="11:00",
            service_id=service.pk,
            client_name="Brand New",
            client_phone="+49000111222",
        )
        assert result["id"] > 0

    def test_missing_service_returns_error(self, db, master, service, provider):
        result = provider.create_quick_appointment(
            resource_id=master.pk,
            booking_date="2026-05-10",
            start_time="10:00",
            service_id=99999,
            client_name="X",
            client_phone="",
        )
        assert result["id"] == 0
        assert "error" in result


# ── update_quick_appointment ──────────────────────────────────────────────────


@pytest.mark.unit
class TestUpdateQuickAppointment:
    def test_updates_datetime(self, db, pending_appointment, provider):
        result = provider.update_quick_appointment(
            booking_id=pending_appointment.pk,
            booking_date="2026-06-15",
            start_time="14:00",
        )
        assert result is not None
        assert result["date"] == "2026-06-15"
        assert result["time"] == "14:00"

    def test_returns_none_for_missing(self, db, provider):
        result = provider.update_quick_appointment(
            booking_id=99999,
            booking_date="2026-06-15",
            start_time="10:00",
        )
        assert result is None


# ── run_cabinet_action ────────────────────────────────────────────────────────


@pytest.mark.unit
class TestRunCabinetAction:
    def test_confirm_action(self, db, pending_appointment, provider):
        with patch("features.conversations.services.notifications._get_engine") as mock_eng:
            mock_eng.return_value = MagicMock()
            result = provider.run_cabinet_action(booking_id=pending_appointment.pk, action="confirm")
        assert result.ok
        assert result.code == "booking-confirm"

    def test_cancel_action(self, db, pending_appointment, provider):
        with patch("features.conversations.services.notifications._get_engine") as mock_eng:
            mock_eng.return_value = MagicMock()
            result = provider.run_cabinet_action(
                booking_id=pending_appointment.pk,
                action="cancel",
                payload={"cancel_reason": "client", "cancel_note": "test"},
            )
        assert result.ok
        assert result.code == "booking-cancel"

    def test_reschedule_action_valid_format(self, db, pending_appointment, provider):
        result = provider.run_cabinet_action(
            booking_id=pending_appointment.pk,
            action="reschedule",
            payload={"datetime_start": "20.06.2026 10:00"},
        )
        assert result.ok
        assert result.code == "booking-reschedule"

    def test_reschedule_action_invalid_format(self, db, pending_appointment, provider):
        result = provider.run_cabinet_action(
            booking_id=pending_appointment.pk,
            action="reschedule",
            payload={"datetime_start": "INVALID"},
        )
        assert not result.ok
        assert result.code == "booking-invalid-format"

    def test_unknown_action(self, db, pending_appointment, provider):
        result = provider.run_cabinet_action(booking_id=pending_appointment.pk, action="fly_to_moon")
        assert not result.ok
        assert result.code == "booking-unknown"

    def test_not_found_returns_error(self, db, provider):
        result = provider.run_cabinet_action(booking_id=99999, action="confirm")
        assert not result.ok
        assert result.code == "booking-not-found"
