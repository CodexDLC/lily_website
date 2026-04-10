"""Tests for BookingSessionService."""

from datetime import date

import pytest
from django.test import RequestFactory
from features.booking.dto import BookingState
from features.booking.services.utils.session import BookingSessionService


class _FakeSession(dict):
    """Dict-like session that supports .modified attribute."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modified = False


def _make_request_with_session(session_data=None):
    """Creates a mock request with a session dict."""
    factory = RequestFactory()
    request = factory.get("/")
    request.session = _FakeSession(session_data or {})
    return request


@pytest.mark.unit
class TestBookingSessionService:
    def test_get_state_returns_default_on_empty_session(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = svc.get_state()
        assert state.step == 1
        assert state.service_id is None
        assert state.master_id is None
        assert state.selected_date is None
        assert state.selected_time is None

    def test_save_and_retrieve_state(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = BookingState(step=3, service_id=5, master_id="42")
        svc.save_state(state)
        retrieved = svc.get_state()
        assert retrieved.step == 3
        assert retrieved.service_id == 5
        assert retrieved.master_id == "42"

    def test_update_from_request_sets_step(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = svc.update_from_request({"step": "2"})
        assert state.step == 2

    def test_update_from_request_ignores_invalid_step(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = svc.update_from_request({"step": "abc"})
        assert state.step == 1  # default

    def test_update_from_request_parses_date(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = svc.update_from_request({"date": "2026-06-15"})
        assert state.selected_date == date(2026, 6, 15)

    def test_update_from_request_parses_time(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = svc.update_from_request({"time": "14:30"})
        assert state.selected_time == "14:30"

    def test_update_from_request_parses_service_id(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = svc.update_from_request({"service_id": "7"})
        assert state.service_id == 7

    def test_update_from_request_sets_master_id(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        state = svc.update_from_request({"master_id": "any"})
        assert state.master_id == "any"

    def test_clear_removes_session_key(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        svc.save_state(BookingState(step=2))
        assert BookingSessionService.SESSION_KEY in request.session
        svc.clear()
        assert BookingSessionService.SESSION_KEY not in request.session

    def test_clear_on_empty_session_is_safe(self):
        request = _make_request_with_session()
        svc = BookingSessionService(request)
        svc.clear()  # Should not raise

    def test_is_valid_for_submission_true(self):
        state = BookingState(step=4, service_id=1, master_id="5", selected_date=date.today(), selected_time="10:00")
        assert state.is_valid_for_submission is True

    def test_is_valid_for_submission_false_missing_time(self):
        state = BookingState(step=3, service_id=1, master_id="5", selected_date=date.today(), selected_time=None)
        assert state.is_valid_for_submission is False

    def test_is_valid_for_submission_false_missing_all(self):
        state = BookingState()
        assert state.is_valid_for_submission is False
