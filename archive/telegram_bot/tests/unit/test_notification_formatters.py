from unittest.mock import MagicMock, patch

import pytest

from src.telegram_bot.features.redis.notifications.resources.dto import BookingNotificationPayload
from src.telegram_bot.features.redis.notifications.resources.formatters import format_new_booking


@pytest.fixture(autouse=True)
def mock_i18n():
    mock = MagicMock()
    mock.notifications.new.booking.title.return_value = "New Booking"
    mock.notifications.new.booking.visits.new.return_value = "New Client"
    mock.notifications.new.booking.details.return_value = "Details: {id}"
    mock.notifications.status.icons.success.return_value = "✅"
    mock.notifications.status.block.return_value = "📧 <b>Email:</b> ✅ Подтверждение записи"
    with patch("aiogram_i18n.I18nContext.get_current", return_value=mock):
        yield mock


def test_format_new_booking_shows_email_notification_label():
    payload = BookingNotificationPayload(
        id=7,
        client_name="Anna",
        first_name="Anna",
        last_name="Test",
        client_phone="+491234",
        client_email="anna@example.com",
        service_name="Manicure",
        master_name="Lily",
        datetime="20.04.2026 10:00",
        duration_minutes=60,
        price=50,
        request_call=False,
    )

    text = format_new_booking(payload, email_status="success", email_label="Подтверждение записи")

    assert "📧 <b>Email:</b> ✅ Подтверждение записи" in text
