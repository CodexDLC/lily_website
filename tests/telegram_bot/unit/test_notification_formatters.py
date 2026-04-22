from src.telegram_bot.features.redis.notifications.resources.dto import BookingNotificationPayload
from src.telegram_bot.features.redis.notifications.resources.formatters import format_new_booking


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
