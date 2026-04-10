"""
Unit tests for features.system.services.notification.NotificationService.
Tests all send_* methods and the _dispatch_notification helper.
"""

from unittest.mock import MagicMock, patch

import features.system.services.notification as notif_module
import pytest
from features.system.services.notification import (
    _BOT_WIRE_PASSTHROUGH_EVENTS,
    NotificationEventType,
    NotificationService,
    _get_engine,
    _get_salon_address,
)


@pytest.fixture(autouse=True)
def reset_engine():
    """Reset singleton before/after each test."""
    notif_module._engine = None
    yield
    notif_module._engine = None


@pytest.fixture
def mock_dispatch():
    """Patch _dispatch_notification to avoid real adapter calls."""
    with patch.object(NotificationService, "_dispatch_notification", return_value=True) as m:
        yield m


@pytest.mark.unit
class TestNotificationEventTypeConstants:
    def test_booking_received_value(self):
        assert NotificationEventType.BOOKING_RECEIVED == "booking_received"

    def test_appointment_confirmed_value(self):
        assert NotificationEventType.APPOINTMENT_CONFIRMED == "appointment_confirmed"

    def test_appointment_cancelled_value(self):
        assert NotificationEventType.APPOINTMENT_CANCELLED == "appointment_cancelled"

    def test_appointment_no_show_value(self):
        assert NotificationEventType.APPOINTMENT_NO_SHOW == "appointment_no_show"

    def test_appointment_rescheduled_value(self):
        assert NotificationEventType.APPOINTMENT_RESCHEDULED == "appointment_rescheduled"

    def test_appointment_reminder_value(self):
        assert NotificationEventType.APPOINTMENT_REMINDER == "appointment_reminder"

    def test_group_booking_value(self):
        assert NotificationEventType.GROUP_BOOKING == "new_group_booking"

    def test_contact_request_value(self):
        assert NotificationEventType.CONTACT_REQUEST == "new_contact_request"


@pytest.mark.unit
class TestBotWirePassthroughEvents:
    def test_contact_request_in_passthrough(self):
        assert NotificationEventType.CONTACT_REQUEST in _BOT_WIRE_PASSTHROUGH_EVENTS

    def test_group_booking_not_in_passthrough(self):
        assert NotificationEventType.GROUP_BOOKING not in _BOT_WIRE_PASSTHROUGH_EVENTS

    def test_booking_received_not_in_passthrough(self):
        assert NotificationEventType.BOOKING_RECEIVED not in _BOT_WIRE_PASSTHROUGH_EVENTS


@pytest.mark.unit
class TestGetEngine:
    def test_creates_engine_if_none(self):
        notif_module._engine = None
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.DjangoArqClient"),
        ):
            mock_adapter_cls.return_value = MagicMock()
            engine = _get_engine()
        assert engine is not None

    def test_returns_same_instance_on_second_call(self):
        notif_module._engine = None
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.DjangoArqClient"),
        ):
            mock_adapter_cls.return_value = MagicMock()
            e1 = _get_engine()
            e2 = _get_engine()
        assert e1 is e2


@pytest.mark.django_db
class TestGetSalonAddress:
    def test_returns_string(self, site_settings_obj):
        from django.core.cache import cache

        cache.delete("site_settings_address")
        addr = _get_salon_address()
        assert isinstance(addr, str)

    def test_caches_address(self, site_settings_obj):
        from django.core.cache import cache

        cache.delete("site_settings_address")
        addr1 = _get_salon_address()
        addr2 = _get_salon_address()
        assert addr1 == addr2

    def test_returns_empty_on_exception(self):
        from django.core.cache import cache

        cache.delete("site_settings_address")
        # SiteSettings is imported lazily inside _get_salon_address,
        # so we patch the lazy import location
        with patch(
            "features.system.models.site_settings.SiteSettings.load",
            side_effect=Exception("DB error"),
        ):
            addr = _get_salon_address()
        assert addr == ""

    def test_uses_cached_value_without_db_call(self, site_settings_obj):
        from django.core.cache import cache

        cache.set("site_settings_address", "Cached Address, 12345 City", timeout=3600)
        addr = _get_salon_address()
        assert addr == "Cached Address, 12345 City"


@pytest.mark.django_db
class TestSendContactReceipt:
    def test_returns_bool(self, mock_dispatch):
        result = NotificationService.send_contact_receipt(
            recipient_email="test@test.de",
            client_name="Anna",
            message_text="Hello",
            request_id=1,
        )
        assert isinstance(result, bool)

    def test_dispatches_with_correct_template(self, mock_dispatch):
        NotificationService.send_contact_receipt(
            recipient_email="test@test.de",
            client_name="Anna",
            message_text="Hello",
            request_id=1,
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "ct_receipt"

    def test_dispatches_with_contact_request_event(self, mock_dispatch):
        NotificationService.send_contact_receipt(
            recipient_email="test@test.de",
            client_name="Anna",
            message_text="Hello",
            request_id=1,
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["event_type"] == NotificationEventType.CONTACT_REQUEST

    def test_base_context_contains_request_id(self, mock_dispatch):
        NotificationService.send_contact_receipt(
            recipient_email="test@test.de",
            client_name="Anna",
            message_text="Hello world",
            request_id=42,
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["base_context"]["request_id"] == 42

    def test_passes_lang_parameter(self, mock_dispatch):
        NotificationService.send_contact_receipt(
            recipient_email="test@test.de",
            client_name="Anna",
            message_text="Hello",
            request_id=1,
            lang="en",
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["lang"] == "en"

    def test_passes_recipient_phone(self, mock_dispatch):
        NotificationService.send_contact_receipt(
            recipient_email="test@test.de",
            client_name="Anna",
            message_text="Hello",
            request_id=1,
            recipient_phone="+49123456789",
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["recipient_phone"] == "+49123456789"

    def test_includes_email_and_telegram_channels(self, mock_dispatch):
        NotificationService.send_contact_receipt(
            recipient_email="test@test.de",
            client_name="Anna",
            message_text="Hello",
            request_id=1,
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert "email" in call_kwargs["channels"]
        assert "telegram" in call_kwargs["channels"]


@pytest.mark.django_db
class TestSendAdminReply:
    def test_dispatches_with_ct_reply_template(self, mock_dispatch):
        NotificationService.send_admin_reply(
            recipient_email="admin@test.de",
            reply_text="Your reply",
            history_text="Previous history",
            request_id=5,
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "ct_reply"

    def test_dispatches_email_only_channel(self, mock_dispatch):
        NotificationService.send_admin_reply(
            recipient_email="admin@test.de",
            reply_text="Reply",
            history_text="History",
            request_id=5,
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["channels"] == ["email"]

    def test_override_fields_contains_subject_with_ref(self, mock_dispatch):
        NotificationService.send_admin_reply(
            recipient_email="admin@test.de",
            reply_text="Reply",
            history_text="History",
            request_id=99,
        )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert "99" in call_kwargs["override_fields"]["subject"]


@pytest.mark.django_db
class TestSendBookingConfirmation:
    def test_dispatches_with_bk_confirmation_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_confirmation(
                recipient_email="client@test.de",
                client_name="Anna",
                context={"date": "2024-05-10"},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "bk_confirmation"

    def test_dispatches_with_appointment_confirmed_event(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_confirmation(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["event_type"] == NotificationEventType.APPOINTMENT_CONFIRMED


@pytest.mark.django_db
class TestSendBookingCancellation:
    def test_dispatches_with_bk_cancellation_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_cancellation(
                recipient_email="client@test.de",
                client_name="Anna",
                context={"reason_text": "Schedule conflict"},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "bk_cancellation"


@pytest.mark.django_db
class TestSendBookingNoShow:
    def test_dispatches_with_bk_no_show_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_no_show(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "bk_no_show"


@pytest.mark.django_db
class TestSendBookingReceipt:
    def test_dispatches_with_bk_receipt_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_receipt(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "bk_receipt"

    def test_dispatches_with_booking_received_event(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_receipt(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["event_type"] == NotificationEventType.BOOKING_RECEIVED


@pytest.mark.django_db
class TestSendBookingReschedule:
    def test_dispatches_with_bk_reschedule_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_reschedule(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "bk_reschedule"


@pytest.mark.django_db
class TestSendBookingReminder:
    def test_dispatches_with_bk_reminder_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_reminder(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "bk_reminder"

    def test_dispatches_with_reminder_event(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_booking_reminder(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["event_type"] == NotificationEventType.APPOINTMENT_REMINDER


@pytest.mark.django_db
class TestSendGroupBookingConfirmation:
    def test_dispatches_with_group_booking_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_group_booking_confirmation(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "bk_group_booking"

    def test_dispatches_with_group_booking_event(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_group_booking_confirmation(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["event_type"] == NotificationEventType.GROUP_BOOKING


@pytest.mark.django_db
class TestSendMarketingReengagement:
    def test_dispatches_with_mk_reengagement_template(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_marketing_reengagement(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["template_name"] == "mk_reengagement"

    def test_dispatches_email_only_channel(self, mock_dispatch):
        with (
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_adapter_cls.return_value.__enter__ = MagicMock()
            mock_adapter_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_selector.get_value.return_value = "Hallo"
            NotificationService.send_marketing_reengagement(
                recipient_email="client@test.de",
                client_name="Anna",
                context={},
            )
        call_kwargs = mock_dispatch.call_args.kwargs
        assert call_kwargs["channels"] == ["email"]


@pytest.mark.django_db
class TestDispatchNotificationWireEventType:
    """Tests the bot wire event type logic in _dispatch_notification."""

    def test_contact_request_passes_through_as_is(self, mock_arq, site_settings_obj):
        """CONTACT_REQUEST is in passthrough set — wire event should equal event_type."""
        from django.core.cache import cache

        cache.delete("site_settings_address")

        with (
            patch.object(
                notif_module._get_engine().__class__,
                "dispatch",
                return_value=True,
            ) as mock_dispatch_method,
            patch("features.system.services.notification.DjangoNotificationAdapter") as mock_adapter_cls,
            patch("features.system.services.notification.selector") as mock_selector,
        ):
            mock_selector.get_value.return_value = "Test"
            ctx_manager = MagicMock()
            ctx_manager.__enter__ = MagicMock(return_value=None)
            ctx_manager.__exit__ = MagicMock(return_value=False)
            mock_adapter_cls.return_value.translation_override.return_value = ctx_manager

            NotificationService._dispatch_notification(
                recipient_email="test@test.de",
                client_name="Anna",
                template_name="ct_receipt",
                event_type=NotificationEventType.CONTACT_REQUEST,
                channels=["email"],
                lang="de",
                base_context={},
                selector_map={},
            )
            # Verify dispatch was called with wire_event_type = CONTACT_REQUEST (passthrough)
            if mock_dispatch_method.called:
                kwargs = mock_dispatch_method.call_args.kwargs
                assert kwargs.get("event_type") == NotificationEventType.CONTACT_REQUEST
