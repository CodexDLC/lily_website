from unittest.mock import ANY, AsyncMock, patch

import pytest

from workers.notification_worker.services.notification_service import NotificationService


@pytest.fixture
def mock_service_args():
    return {
        "templates_dir": "/tmp/templates",
        "site_url": "https://lily.de",
        "logo_url": "logo.png",
        "smtp_host": "localhost",
        "smtp_port": 587,
        "smtp_from_email": "no-reply@lily.de",
    }


@pytest.fixture
def notification_service(mock_service_args):
    with (
        patch("workers.notification_worker.services.notification_service.AsyncEmailClient"),
        patch("workers.notification_worker.services.notification_service.TemplateRenderer"),
    ):
        return NotificationService(**mock_service_args)


class TestNotificationService:
    def test_init_missing_args(self):
        with pytest.raises(ValueError, match="Core SMTP settings are missing"):
            NotificationService(templates_dir=".", site_url=".", smtp_host=None, smtp_port=None, smtp_from_email=None)

    def test_resolve_template_path(self, notification_service):
        assert notification_service.resolve_template_path("bk_confirm") == "booking/bk_confirm.html"
        assert notification_service.resolve_template_path("ct_form") == "contacts/ct_form.html"
        assert notification_service.resolve_template_path("mk_promo") == "marketing/mk_promo.html"
        assert notification_service.resolve_template_path("other") == "other.html"
        assert notification_service.resolve_template_path("custom.html") == "custom.html"

    def test_get_absolute_logo_url(self, notification_service):
        notification_service.logo_url = "logo.png"
        assert notification_service.get_absolute_logo_url() == "https://lily.de/logo.png"

        notification_service.logo_url = "http://external.com/logo.png"
        assert notification_service.get_absolute_logo_url() == "http://external.com/logo.png"

        notification_service.logo_url = None
        assert "/static/img/_source/logo_lily.png" in notification_service.get_absolute_logo_url()

    def test_enrich_email_context(self, notification_service):
        data = {"first_name": "Anna", "datetime": "20.04.2026 10:00", "visits_count": 0, "name": "Anna Testova"}
        enriched = notification_service.enrich_email_context(data)

        assert enriched["date"] == "20.04.2026"
        assert enriched["time"] == "10:00"
        assert enriched["site_url"] == "https://lily.de"
        assert enriched["greeting"] == "Sehr geehrte/r Anna Testova,"
        assert "calendar_url" in enriched

    @pytest.mark.asyncio
    async def test_send_notification(self, notification_service):
        # Mock renderer and email client
        notification_service.renderer.render.return_value = "<html><body>Test</body></html>"
        notification_service.email_client.send_email = AsyncMock()

        await notification_service.send_notification(
            email="test@user.com", subject="Test Subject", template_name="bk_confirm", data={"first_name": "Anna"}
        )

        notification_service.renderer.render.assert_called_once()
        notification_service.email_client.send_email.assert_called_once_with(
            "test@user.com", "Test Subject", "<html><body>Test</body></html>", headers=None
        )

    @pytest.mark.asyncio
    async def test_legacy_send_methods(self, notification_service):
        notification_service.send_notification = AsyncMock()
        context = {"datetime": "20.04.2026 10:00"}

        await notification_service.send_booking_confirmation("a@b.com", "Anna", context)
        notification_service.send_notification.assert_called_with("a@b.com", ANY, "bk_confirmation", ANY)

        await notification_service.send_booking_cancellation("a@b.com", "Anna", context)
        notification_service.send_notification.assert_called_with("a@b.com", ANY, "bk_cancellation", ANY)

        await notification_service.send_booking_no_show("a@b.com", "Anna", context)
        notification_service.send_notification.assert_called_with("a@b.com", ANY, "bk_no_show", ANY)

        await notification_service.send_universal("a@b.com", "Anna", "template", "subject", context)
        notification_service.send_notification.assert_called_with("a@b.com", "subject", "template", ANY)

    def test_enrich_context_greeting_logic(self, notification_service):
        # New client (0 visits)
        ctx = notification_service.enrich_email_context({"name": "Anna", "visits_count": 0})
        assert "Sehr geehrte/r Anna" in ctx["greeting"]

        # Regular client (2 visits)
        ctx = notification_service.enrich_email_context({"name": "Anna", "visits_count": 2})
        assert "Liebe/r Anna" in ctx["greeting"]

        # Loyal client (10 visits)
        ctx = notification_service.enrich_email_context({"name": "Anna", "visits_count": 10})
        assert "Hallo Anna" in ctx["greeting"]

    def test_enrich_context_date_fallback(self, notification_service):
        ctx = notification_service.enrich_email_context({"datetime": "invalid", "booking_date": "20.04.2026"})
        assert ctx["date"] == "20.04.2026"
        assert ctx["time"] == ""


class TestMessageBuilder:
    def test_get_sms_text_success(self):
        from workers.notification_worker.services.notification_service import MessageBuilder

        data = {"first_name": "Anna", "datetime": "20.04.2026 10:00"}
        text = MessageBuilder.get_sms_text(data)
        assert "Anna" in text
        assert "20.04.2026" in text
        assert "10:00" in text

    def test_get_sms_text_fallback(self):
        from workers.notification_worker.services.notification_service import MessageBuilder

        data = {"first_name": "Anna", "datetime": "invalid"}
        text = MessageBuilder.get_sms_text(data)
        assert "Anna" in text
        assert "invalid" in text


class TestCalendarUrlBuilder:
    def test_build_url_success(self):
        from workers.notification_worker.services.notification_service import CalendarUrlBuilder

        data = {
            "datetime": "20.04.2026 10:00",
            "service_name": "Manicure",
            "duration_minutes": 60,
            "salon_address": "Berlin",
        }
        url = CalendarUrlBuilder.build_url(data, site_url="https://lily.de")
        assert "action=TEMPLATE" in url
        assert "Berlin" in url
        assert "Manicure" in url

    def test_build_url_missing_datetime(self):
        from workers.notification_worker.services.notification_service import CalendarUrlBuilder

        assert CalendarUrlBuilder.build_url({}, site_url=".") == ""

    def test_build_url_invalid_datetime(self):
        from workers.notification_worker.services.notification_service import CalendarUrlBuilder

        assert CalendarUrlBuilder.build_url({"datetime": "invalid"}, site_url=".") == ""
