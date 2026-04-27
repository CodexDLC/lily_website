import pytest
from unittest.mock import AsyncMock, MagicMock
from src.workers.notification_worker.services.notification_service import NotificationService

@pytest.fixture
def service():
    return NotificationService(
        templates_dir=".",
        site_url="http://site.com",
        smtp_host="localhost",
        smtp_port=25,
        smtp_from_email="noreply@site.com"
    )

@pytest.mark.asyncio
async def test_send_rendered_notification(service):
    service.email_client.send_email = AsyncMock()
    await service.send_rendered_notification("test@test.com", "Subj", "<html></html>")
    service.email_client.send_email.assert_called_once()

def test_get_sms_text_compat(service):
    data = {"first_name": "Anna", "datetime": "27.04.2026 14:00"}
    res = service.get_sms_text(data)
    assert "Anna" in res
    assert "27.04.2026" in res

def test_generate_google_calendar_url_compat(service):
    data = {"datetime": "27.04.2026 14:00", "service_name": "Haircut"}
    res = service._generate_google_calendar_url(data)
    assert "google.com/calendar" in res
    assert "Haircut" in res
