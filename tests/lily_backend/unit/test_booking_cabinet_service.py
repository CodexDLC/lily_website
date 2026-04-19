"""Unit tests for features/booking/services/cabinet.py.

All provider and settings calls are mocked — no DB access required.
"""

from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock, patch

import pytest


def _mock_provider() -> MagicMock:
    prov = MagicMock()
    prov.get_cabinet_masters.return_value = [
        {"id": 1, "name": "Lily Master"},
        {"id": 2, "name": "Rose Master"},
    ]
    prov.get_cabinet_appointments.return_value = []
    prov.get_cabinet_clients.return_value = [
        {"id": 1, "name": "Anna T", "phone": "+49111", "email": "a@t.de"},
    ]
    prov.get_cabinet_services.return_value = [
        {
            "id": 10,
            "title": "Cut",
            "price": 50.0,
            "duration": 60,
            "category": "nails",
            "master_ids": [1],
            "conflicts_with": [],
            "conflict_rules": [],
        }
    ]
    prov.get_service_categories.return_value = []
    prov.get_quick_create_services.return_value = [
        MagicMock(value="10"),
    ]
    prov.get_quick_create_clients.return_value = []
    prov.get_schedule_prefill.return_value = MagicMock(
        resource_id=1,
        resource_name="Lily Master",
        booking_date="2026-05-11",
        start_time="09:00",
    )
    prov.get_quick_create_slot_options.return_value = ["09:00", "09:30", "10:00"]
    prov.create_quick_client.return_value = {"id": 99, "name": "New", "phone": "", "email": ""}
    prov.create_quick_appointment.return_value = {"id": 42, "error": None}
    prov.run_cabinet_action.return_value = MagicMock(ok=True, code="ok")
    return prov


def _mock_settings() -> MagicMock:
    s = MagicMock()
    s.max_advance_days = 30
    s.step_minutes = 30
    s.get_day_schedule.return_value = (time(9, 0), time(18, 0))
    s.book_only_from_next_day = False
    return s


def _make_workflow(provider=None, settings=None):
    from features.booking.services.cabinet import BookingCabinetWorkflowService

    prov = provider or _mock_provider()
    s = settings or _mock_settings()
    with (
        patch("features.booking.booking_settings.BookingSettings.load", return_value=s),
        patch("features.booking.services.cabinet.CabinetBookingAvailabilityService"),
    ):
        svc = BookingCabinetWorkflowService(provider=prov)
    return svc, prov, s


def _make_bridge(provider=None):
    from features.booking.services.cabinet import BookingCabinetBridgeAdapter

    prov = provider or _mock_provider()
    return BookingCabinetBridgeAdapter(provider=prov), prov


# ── BookingCabinetWorkflowService ─────────────────────────────────────────────


@pytest.mark.unit
class TestWorkflowStaticHelpers:
    def test_get_client_color_deterministic(self):
        from features.booking.services.cabinet import BookingCabinetWorkflowService

        c1 = BookingCabinetWorkflowService._get_client_color("Anna")
        c2 = BookingCabinetWorkflowService._get_client_color("Anna")
        assert c1 == c2
        assert c1.startswith("hsla(")

    def test_get_client_border_deterministic(self):
        from features.booking.services.cabinet import BookingCabinetWorkflowService

        b = BookingCabinetWorkflowService._get_client_border("Max")
        assert b.startswith("hsl(")

    def test_colors_differ_for_different_names(self):
        from features.booking.services.cabinet import BookingCabinetWorkflowService

        c1 = BookingCabinetWorkflowService._get_client_color("Anna")
        c2 = BookingCabinetWorkflowService._get_client_color("Boris")
        assert c1 != c2


@pytest.mark.unit
class TestGetScheduleContext:
    def _request(self, date: str | None = None) -> MagicMock:
        import datetime as dt

        today = dt.date.today().strftime("%Y-%m-%d")
        req = MagicMock()
        req.GET.get.side_effect = lambda k, d=today: (date if date is not None else today) if k == "date" else d
        return req

    def test_basic_returns_calendar(self):
        svc, prov, _ = _make_workflow()
        ctx = svc.get_schedule_context(self._request())
        assert "calendar" in ctx
        assert "rows" in ctx
        assert len(ctx["rows"]) > 0

    def test_with_explicit_date(self):
        svc, prov, _ = _make_workflow()
        ctx = svc.get_schedule_context(self._request("2026-05-11"))
        assert ctx["calendar"].title == "2026-05-11"

    def test_today_keyword(self):
        svc, prov, _ = _make_workflow()
        req = MagicMock()
        req.GET.get.return_value = "today"
        ctx = svc.get_schedule_context(req)
        today_str = datetime.today().strftime("%Y-%m-%d")
        assert ctx["calendar"].title == today_str

    def test_closed_day_falls_back_to_first_open(self):
        # Day schedule returns None for weekday 0, but (9,18) for others
        svc, prov, s = _make_workflow()
        s.get_day_schedule.side_effect = lambda wd: (time(9, 0), time(18, 0)) if wd != 0 else None
        # Monday 2026-05-11 weekday=0 → fallback to Tuesday schedule
        ctx = svc.get_schedule_context(self._request("2026-05-11"))
        assert "rows" in ctx

    def test_appointments_rendered_as_calendar_slots(self):
        prov = _mock_provider()
        prov.get_cabinet_appointments.return_value = [
            {
                "id": 1,
                "master_id": 1,
                "date": "2026-05-11",
                "time": "10:00",
                "duration": 60,
                "client_name": "Anna",
                "status": "confirmed",
                "service_title": "Cut",
                "price": 50,
                "admin_notes": "",
                "client_notes": "pls fast",
                "client_created_at": None,
            }
        ]
        svc, _, _ = _make_workflow(provider=prov)
        ctx = svc.get_schedule_context(self._request("2026-05-11"))
        assert len(ctx["calendar"].events) == 1

    def test_appointment_with_new_client_badge(self):
        prov = _mock_provider()
        recent_dt = (datetime.now() - timedelta(days=1)).isoformat()
        prov.get_cabinet_appointments.return_value = [
            {
                "id": 2,
                "master_id": 1,
                "date": "2026-05-11",
                "time": "11:00",
                "duration": 30,
                "client_name": "Brand New",
                "status": "pending",
                "service_title": "Cut",
                "price": 50,
                "admin_notes": "",
                "client_notes": "",
                "client_created_at": recent_dt,
            }
        ]
        svc, _, _ = _make_workflow(provider=prov)
        ctx = svc.get_schedule_context(self._request("2026-05-11"))
        slot = ctx["calendar"].events[0]
        assert any(d["text"] == "New Client" for d in slot.details)

    def test_appointment_long_duration_indicator(self):
        prov = _mock_provider()
        prov.get_cabinet_appointments.return_value = [
            {
                "id": 3,
                "master_id": 1,
                "date": "2026-05-11",
                "time": "09:00",
                "duration": 120,  # >60 → clock indicator
                "client_name": "Client",
                "status": "pending",
                "service_title": "Cut",
                "price": 50,
                "admin_notes": "",
                "client_notes": "",
                "client_created_at": None,
            }
        ]
        svc, _, _ = _make_workflow(provider=prov)
        ctx = svc.get_schedule_context(self._request("2026-05-11"))
        slot = ctx["calendar"].events[0]
        assert "bi-clock-history" in slot.indicators

    def test_appointment_unknown_master_skipped(self):
        prov = _mock_provider()
        prov.get_cabinet_appointments.return_value = [
            {
                "id": 4,
                "master_id": 99,  # not in masters list
                "date": "2026-05-11",
                "time": "10:00",
                "duration": 60,
                "client_name": "X",
                "status": "pending",
                "service_title": "Cut",
                "price": 0,
                "admin_notes": "",
                "client_notes": "",
                "client_created_at": None,
            }
        ]
        svc, _, _ = _make_workflow(provider=prov)
        ctx = svc.get_schedule_context(self._request("2026-05-11"))
        assert ctx["calendar"].events == []


@pytest.mark.unit
class TestGetNewBookingContext:
    def _request(self, mode: str = "single") -> MagicMock:
        req = MagicMock()
        req.GET.get.return_value = mode
        return req

    def test_single_mode(self):
        svc, _, _ = _make_workflow()
        svc.availability.build_picker_days.return_value = []
        ctx = svc.get_new_booking_context(self._request("single"))
        assert ctx["builder_mode"] == "single"
        assert "selector" in ctx
        assert "picker" in ctx

    def test_separate_mode(self):
        svc, _, _ = _make_workflow()
        svc.availability.build_picker_days.return_value = []
        ctx = svc.get_new_booking_context(self._request("separate"))
        assert ctx["builder_mode"] == "separate"
        assert "separate_services" in ctx

    def test_series_mode(self):
        svc, _, _ = _make_workflow()
        svc.availability.build_picker_days.return_value = []
        ctx = svc.get_new_booking_context(self._request("series"))
        assert ctx["builder_mode"] == "series"
        assert "series_services" in ctx


@pytest.mark.unit
class TestCreateNewBooking:
    def _request(self, payload: dict) -> MagicMock:
        req = MagicMock()
        req.POST.get.return_value = json.dumps(payload)
        return req

    def test_invalid_json_returns_error(self):
        svc, _, _ = _make_workflow()
        req = MagicMock()
        req.POST.get.return_value = "INVALID{JSON}"
        result = svc.create_new_booking(req)
        assert not result["ok"]
        assert "Invalid" in result["message"]

    def test_no_services_returns_error(self):
        svc, _, _ = _make_workflow()
        result = svc.create_new_booking(
            self._request({"mode": "single", "date": "2026-05-11", "time": "10:00", "services": []})
        )
        assert not result["ok"]

    def test_missing_date_returns_error(self):
        svc, _, _ = _make_workflow()
        result = svc.create_new_booking(
            self._request({"mode": "single", "date": "", "time": "", "services": [{"id": 10}], "client": {}})
        )
        assert not result["ok"]

    def test_single_mode_creates_appointment(self):
        prov = _mock_provider()
        prov.create_quick_appointment.return_value = {"id": 5}
        svc, _, _ = _make_workflow(provider=prov)
        result = svc.create_new_booking(
            self._request(
                {
                    "mode": "single",
                    "date": "2026-05-11",
                    "time": "10:00",
                    "services": [{"id": "10", "masterId": 1}],
                    "client": {"name": "Anna Test", "phone": "+49111", "email": ""},
                }
            )
        )
        assert result["ok"]
        assert len(result["created"]) == 1

    def test_single_mode_with_existing_client_id(self):
        prov = _mock_provider()
        prov.create_quick_appointment.return_value = {"id": 6}
        svc, _, _ = _make_workflow(provider=prov)
        result = svc.create_new_booking(
            self._request(
                {
                    "mode": "single",
                    "date": "2026-05-11",
                    "time": "10:00",
                    "services": [{"id": "10"}],
                    "client": {"id": "1"},  # existing client id
                }
            )
        )
        assert result["ok"]

    def test_separate_mode_creates_per_service_appointments(self):
        prov = _mock_provider()
        prov.create_quick_appointment.return_value = {"id": 7}
        svc, _, _ = _make_workflow(provider=prov)
        result = svc.create_new_booking(
            self._request(
                {
                    "mode": "separate",
                    "date": "",
                    "time": "",
                    "services": [{"id": "10", "date": "2026-05-11", "time": "10:00", "masterId": 1}],
                    "client": {"name": "Max", "phone": "+49999", "email": ""},
                }
            )
        )
        assert result["ok"]


@pytest.mark.unit
class TestGetListContext:
    def _appt(self, status: str = "pending") -> dict:
        return {
            "id": 1,
            "master_id": 1,
            "date": "2026-05-11",
            "time": "10:00",
            "duration": 60,
            "client_name": "Anna",
            "status": status,
            "service_title": "Cut",
            "price": 50,
            "admin_notes": "",
            "client_notes": "",
            "client_created_at": None,
        }

    def test_no_filter_returns_all(self):
        prov = _mock_provider()
        prov.get_cabinet_appointments.return_value = [
            self._appt("pending"),
            self._appt("confirmed"),
        ]
        svc, _, _ = _make_workflow(provider=prov)
        ctx = svc.get_list_context(MagicMock())
        assert len(ctx["appointments"]) == 2
        assert ctx["counts"]["all"] == 2

    def test_status_filter(self):
        prov = _mock_provider()
        prov.get_cabinet_appointments.return_value = [
            self._appt("pending"),
            self._appt("confirmed"),
        ]
        svc, _, _ = _make_workflow(provider=prov)
        ctx = svc.get_list_context(MagicMock(), status="pending")
        assert len(ctx["appointments"]) == 1
        assert ctx["appointments"][0]["status"] == "pending"

    def test_appointments_have_master_name(self):
        prov = _mock_provider()
        prov.get_cabinet_appointments.return_value = [self._appt("confirmed")]
        svc, _, _ = _make_workflow(provider=prov)
        ctx = svc.get_list_context(MagicMock())
        row = ctx["appointments"][0]
        assert row["master_name"] == "Lily Master"
        assert "status_label" in row
        assert "status_color" in row


# ── BookingCabinetBridgeAdapter ───────────────────────────────────────────────


@pytest.mark.unit
class TestBridgeAdapterHelpers:
    def test_build_profile(self):
        from features.booking.services.cabinet import BookingCabinetBridgeAdapter

        profile = BookingCabinetBridgeAdapter._build_profile(
            {
                "client_name": "Anna Test",
                "phone": "+49111",
            }
        )
        assert profile.name == "Anna Test"
        assert profile.avatar == "AT"

    def test_build_summary(self):
        from features.booking.services.cabinet import BookingCabinetBridgeAdapter

        items = BookingCabinetBridgeAdapter._build_summary(
            {
                "service_title": "Cut",
                "status": "pending",
                "date": "2026-05-11",
                "time": "10:00",
                "price": 50,
            }
        )
        assert len(items) == 4
        assert items[0].label == "Service"
        assert items[0].value == "Cut"

    def test_shift_date_forward(self):
        from features.booking.services.cabinet import BookingCabinetBridgeAdapter

        result = BookingCabinetBridgeAdapter._shift_date("2026-05-11", days=3)
        assert result == "2026-05-14"

    def test_shift_date_backward(self):
        from features.booking.services.cabinet import BookingCabinetBridgeAdapter

        result = BookingCabinetBridgeAdapter._shift_date("2026-05-11", days=-1)
        assert result == "2026-05-10"


@pytest.mark.unit
class TestBridgeGetModalState:
    def _appt_dict(self) -> dict:
        return {
            "id": 10,
            "master_id": 1,
            "date": "2026-05-11",
            "time": "10:00",
            "duration": 60,
            "client_name": "Anna Test",
            "phone": "+49111",
            "status": "pending",
            "service_title": "Cut",
            "price": 50,
            "admin_notes": "",
            "client_notes": "",
        }

    def _req(self, date: str = "", col: int = 0, row: int = 0) -> MagicMock:
        req = MagicMock()
        req.GET.get.side_effect = lambda k, d="": {"date": date, "col": str(col), "row": str(row)}.get(k, d)
        return req

    def test_mode_create_from_slot(self):
        bridge, prov = _make_bridge()
        req = self._req(date="2026-05-11")
        state = bridge.get_modal_state(req, booking_id=0, mode="create_from_slot")
        assert state.mode == "create_from_slot"
        assert state.booking_id == 0
        assert state.quick_create is not None

    def test_mode_not_found(self):
        bridge, prov = _make_bridge()
        prov.get_cabinet_appointments.return_value = []  # empty → not found
        state = bridge.get_modal_state(self._req(), booking_id=99, mode="detail")
        assert state.title == "Not Found"

    def test_mode_detail_pending_has_confirm_action(self):
        bridge, prov = _make_bridge()
        prov.get_cabinet_appointments.return_value = [self._appt_dict()]
        state = bridge.get_modal_state(self._req(), booking_id=10, mode="detail")
        action_values = [a.value for a in state.actions]
        assert "confirm" in action_values

    def test_mode_confirm(self):
        bridge, prov = _make_bridge()
        prov.get_cabinet_appointments.return_value = [self._appt_dict()]
        state = bridge.get_modal_state(self._req(), booking_id=10, mode="confirm")
        assert state.mode == "confirm"
        assert state.form is not None
        assert any(a.value == "confirm" for a in state.actions)

    def test_mode_cancel(self):
        bridge, prov = _make_bridge()
        prov.get_cabinet_appointments.return_value = [self._appt_dict()]
        state = bridge.get_modal_state(self._req(), booking_id=10, mode="cancel")
        assert state.mode == "cancel"
        assert state.form is not None
        assert any(a.value == "cancel" for a in state.actions)

    def test_mode_reschedule(self):
        bridge, prov = _make_bridge()
        prov.get_cabinet_appointments.return_value = [self._appt_dict()]
        state = bridge.get_modal_state(self._req(date="2026-05-12"), booking_id=10, mode="reschedule")
        assert state.mode == "reschedule"
        assert state.slot_picker is not None

    def test_mode_detail_confirmed_no_confirm_action(self):
        bridge, prov = _make_bridge()
        appt = {**self._appt_dict(), "status": "confirmed"}
        prov.get_cabinet_appointments.return_value = [appt]
        state = bridge.get_modal_state(self._req(), booking_id=10, mode="detail")
        action_values = [a.value for a in state.actions]
        assert "confirm" not in action_values


@pytest.mark.unit
class TestBridgeExecuteAction:
    def _appt_dict(self) -> dict:
        return {
            "id": 10,
            "master_id": 1,
            "date": "2026-05-11",
            "time": "10:00",
            "duration": 60,
            "client_name": "Anna Test",
            "phone": "+49111",
            "status": "pending",
            "service_title": "Cut",
            "price": 50,
        }

    def test_create_from_slot_with_existing_client(self):
        bridge, prov = _make_bridge()
        prov.create_quick_appointment.return_value = {"id": 42, "error": None}
        prov.run_cabinet_action.return_value = MagicMock(ok=True)

        result = bridge.execute_action(
            MagicMock(),
            booking_id=0,
            action="create_from_slot",
            payload={
                "client_id": "1",  # matches cabinet_clients[0]
                "resource_id": 1,
                "date": "2026-05-11",
                "time": "10:00",
                "service_id": 10,
            },
        )
        assert result.ok
        prov.create_quick_appointment.assert_called_once()

    def test_create_from_slot_with_new_client(self):
        bridge, prov = _make_bridge()
        prov.create_quick_appointment.return_value = {"id": 43, "error": None}
        prov.run_cabinet_action.return_value = MagicMock(ok=True)

        result = bridge.execute_action(
            MagicMock(),
            booking_id=0,
            action="create_from_slot",
            payload={
                "client_id": "new",
                "client_first_name": "Max",
                "client_last_name": "Mustermann",
                "client_phone": "+49999",
                "client_email": "",
                "resource_id": 1,
                "date": "2026-05-11",
                "time": "11:00",
                "service_id": 10,
            },
        )
        assert result.ok
        prov.create_quick_client.assert_called_once()

    def test_create_from_slot_no_client_name_returns_error(self):
        bridge, prov = _make_bridge()
        prov.run_cabinet_action.return_value = MagicMock(ok=False)

        bridge.execute_action(
            MagicMock(),
            booking_id=0,
            action="create_from_slot",
            payload={
                "client_id": "new",
                "client_first_name": "",
                "client_last_name": "",
                "client_phone": "",
                "client_email": "",
                "resource_id": 1,
                "date": "2026-05-11",
                "time": "11:00",
                "service_id": 10,
            },
        )
        prov.run_cabinet_action.assert_called_with(
            booking_id=0,
            action="unsupported",
            redirect_url=bridge._modal_url(0, mode="create_from_slot") + "&date=2026-05-11",
        )

    def test_reschedule_action(self):
        bridge, prov = _make_bridge()
        prov.update_quick_appointment.return_value = {"id": 10}
        prov.run_cabinet_action.return_value = MagicMock(ok=True)

        result = bridge.execute_action(
            MagicMock(),
            booking_id=10,
            action="reschedule",
            payload={"date": "2026-06-01", "time": "14:00"},
        )
        assert result.ok
        prov.update_quick_appointment.assert_called_once_with(
            booking_id=10, booking_date="2026-06-01", start_time="14:00"
        )

    def test_generic_action_delegates_to_provider(self):
        bridge, prov = _make_bridge()
        prov.run_cabinet_action.return_value = MagicMock(ok=True, code="booking-cancel")

        result = bridge.execute_action(MagicMock(), booking_id=10, action="cancel", payload={})
        assert result.code == "booking-cancel"
        prov.run_cabinet_action.assert_called_once_with(
            booking_id=10, action="cancel", redirect_url=bridge._modal_url(10)
        )


@pytest.mark.unit
class TestGetBookingBridgeAndWorkflow:
    def test_get_booking_bridge_returns_singleton(self):
        from features.booking.services.cabinet import get_booking_bridge

        b1 = get_booking_bridge()
        b2 = get_booking_bridge()
        assert b1 is b2

    def test_get_booking_cabinet_workflow_singleton(self):
        import features.booking.services.cabinet as cab_module
        from features.booking.services.cabinet import (
            get_booking_cabinet_workflow,
        )

        # Reset singleton so the test creates a fresh one
        cab_module._cabinet_workflow = None
        with (
            patch("features.booking.booking_settings.BookingSettings.load", return_value=_mock_settings()),
            patch("features.booking.services.cabinet.CabinetBookingAvailabilityService"),
        ):
            w = get_booking_cabinet_workflow()
        assert w is get_booking_cabinet_workflow()
