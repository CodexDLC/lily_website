from unittest.mock import MagicMock, patch

import pytest
from cabinet.booking_bridge import BookingModalActionState, BookingModalState
from django.http import HttpRequest
from django.urls import reverse
from features.booking.booking_settings import BookingSettings

from src.lily_backend.cabinet.services.booking import BookingService


@pytest.mark.django_db
class TestBookingServiceWrapper:
    def test_get_or_create_settings_exists(self):
        # Create settings in DB
        BookingSettings.objects.get_or_create(pk=1)
        instance, error = BookingService.get_or_create_settings()
        assert instance.pk == 1
        assert error is None

    @patch("features.booking.booking_settings.BookingSettings.objects.get_or_create")
    def test_get_or_create_settings_error(self, mock_get_or_create):
        from django.db import OperationalError

        mock_get_or_create.side_effect = OperationalError("DB down")
        instance, error = BookingService.get_or_create_settings()
        assert isinstance(instance, BookingSettings)
        assert "storage is not available" in error

    def test_modal_url(self):
        url = BookingService.modal_url(123)
        assert "/cabinet/booking/123/modal/" in url

        url_with_mode = BookingService.modal_url(123, mode="edit")
        assert "mode=edit" in url_with_mode

    @patch("src.lily_backend.cabinet.services.booking.get_booking_cabinet_workflow")
    def test_workflow_wrappers(self, mock_workflow_factory):
        mock_workflow = MagicMock()
        mock_workflow_factory.return_value = mock_workflow
        req = HttpRequest()

        BookingService.get_schedule_context(req)
        mock_workflow.get_schedule_context.assert_called_once_with(req)

        BookingService.get_new_booking_context(req)
        mock_workflow.get_new_booking_context.assert_called_once_with(req)

        BookingService.get_list_context(req, status="pending")
        mock_workflow.get_list_context.assert_called_once_with(req, status="pending")

        BookingService.create_new_booking(req)
        mock_workflow.create_new_booking.assert_called_once_with(req)

    def test_build_modal_action_open_mode(self):
        action = BookingModalActionState(kind="open_mode", value="edit", label="Edit", method="GET", style="primary")
        modal_action = BookingService._build_modal_action(123, action)
        assert modal_action.label == "Edit"
        assert "mode=edit" in modal_action.url

    def test_build_modal_action_execute(self):
        action = BookingModalActionState(
            kind="execute", value="confirm", label="Confirm", method="POST", style="success"
        )
        modal_action = BookingService._build_modal_action(123, action)
        assert modal_action.label == "Confirm"
        assert reverse("cabinet:booking_action", kwargs={"pk": 123, "action": "confirm"}) in modal_action.url

    def test_build_modal_action_default(self):
        action = BookingModalActionState(kind="close", value="", label="Close", method="CLOSE", style="secondary")
        modal_action = BookingService._build_modal_action(123, action)
        assert modal_action.method == "CLOSE"

    @patch("src.lily_backend.cabinet.services.booking.get_booking_bridge")
    def test_get_booking_modal_context(self, mock_bridge_factory):
        mock_bridge = MagicMock()
        mock_bridge_factory.return_value = mock_bridge

        # Mock state
        state = BookingModalState(
            booking_id=123,
            title="Test Modal",
            mode="detail",
            profile=MagicMock(name="John", subtitle="Client", avatar=None),
            summary_items=[MagicMock(label="Date", value="Today")],
            form=MagicMock(
                fields=[MagicMock(name="f1", label="L1", field_type="text", placeholder="", value="", options=[])]
            ),
            slot_picker=MagicMock(
                selected_date="2026-01-01",
                selected_date_label="Jan 1",
                selected_time="10:00",
                prev_url="",
                next_url="",
                today_url="",
                calendar_url="",
                slots=[MagicMock(value="10:00", label="10:00", available=True)],
            ),
            quick_create=MagicMock(
                prefill=MagicMock(resource_name="R1", booking_date="2026-01-01", start_time="10:00", resource_id=1),
                service_options=[MagicMock(value="1", label="S1", price_label="10", duration_label="30")],
                client_options=[MagicMock(value="1", label="C1", subtitle="S", email="e", search_text="s")],
                selected_service_id="1",
                selected_client_id="1",
                client_search_query="",
                client_search_min_chars=3,
                new_client_first_name="",
                new_client_last_name="",
                new_client_phone="",
                new_client_email="",
                allow_new_client=True,
            ),
            chain_preview=MagicMock(title="Chain", items=[MagicMock(title="I1", subtitle="S1", meta="M1")]),
            actions=[
                BookingModalActionState(kind="open_mode", value="detail", label="D", method="GET", style="primary")
            ],
        )
        mock_bridge.get_modal_state.return_value = state

        req = HttpRequest()
        req.GET = {"mode": "detail"}

        ctx = BookingService.get_booking_modal_context(req, 123)
        assert "obj" in ctx
        modal_content = ctx["obj"]
        assert modal_content.title == "Test Modal"
        # Check sections exist
        assert len(modal_content.sections) == 7  # profile, summary, form, slot_picker, quick_create, chain, actions

    @patch("src.lily_backend.cabinet.services.booking.get_booking_bridge")
    def test_perform_action(self, mock_bridge_factory):
        mock_bridge = MagicMock()
        mock_bridge_factory.return_value = mock_bridge

        mock_result = MagicMock(ok=True, code="ok", message="Success", field_errors={}, ui_effect=None, target_url="/")
        mock_bridge.execute_action.return_value = mock_result

        req = HttpRequest()
        req.POST = {"data": "1"}

        res = BookingService.perform_action(req, 123, "confirm")
        assert res["ok"] is True
        assert res["code"] == "ok"
        mock_bridge.execute_action.assert_called_once()
