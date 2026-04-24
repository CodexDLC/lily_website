from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from codex_bot.base import UnifiedViewDTO, ViewResultDTO

from src.telegram_bot.features.redis.notifications.logic.booking_processor import BookingProcessor
from src.telegram_bot.features.redis.notifications.logic.contact_processor import ContactProcessor
from src.telegram_bot.features.redis.notifications.logic.orchestrator import NotificationsOrchestrator


@pytest.fixture(autouse=True)
def mock_i18n_global():
    mock_i18n = MagicMock()
    mock_i18n.notifications.new.booking.title.return_value = "New Booking"
    mock_i18n.notifications.new.booking.visits.new.return_value = "New Client"
    mock_i18n.notifications.new.booking.visits.regular.return_value = "Regular Client"
    mock_i18n.notifications.new.booking.details.return_value = "Details"
    mock_i18n.notifications.new.booking.promo.return_value = "Promo"
    mock_i18n.notifications.status.icons.sent.return_value = "✅"
    mock_i18n.notifications.status.icons.waiting.return_value = "⏳"
    mock_i18n.notifications.status.icons.none.return_value = "❓"
    mock_i18n.notifications.status.block.return_value = "Status Block"
    mock_i18n.notifications.alert.deleted.return_value = "Deleted"
    mock_i18n.notifications.new.contact.preview.text.return_value = "New Contact Preview"
    mock_i18n.notifications.btn.open.crm.return_value = "Open CRM"
    mock_i18n.notifications.btn.delete.return_value = "Delete"
    mock_i18n.notifications.btn.open.bot.return_value = "Open Bot"
    mock_i18n.notifications.error.api.return_value = "Error processing notification: API Error"

    with patch("aiogram_i18n.I18nContext.get_current", return_value=mock_i18n):
        yield mock_i18n


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.site_settings.aget_field = AsyncMock(return_value="https://test.com")
    container.redis.appointment_cache.get = AsyncMock()
    container.redis.appointment_cache.save = AsyncMock()
    container.redis.appointment_cache.delete = AsyncMock()
    container.redis.contact_cache.save = AsyncMock()
    container.redis.contact_cache.delete = AsyncMock()
    container.redis.sender.clear_coords = AsyncMock()
    container.view_sender.send = AsyncMock()
    return container


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.telegram_admin_channel_id = -100123
    settings.telegram_notification_topic_id = 10
    settings.telegram_topics = {"termin": 10, "contact": 20}
    return settings


class TestBookingProcessor:
    @pytest.mark.asyncio
    async def test_handle_notification_success(self, mock_settings, mock_container):
        processor = BookingProcessor(mock_settings, mock_container)
        payload = {
            "id": 123,
            "client_name": "Test Client",
            "client_phone": "123456",
            "client_email": "test@test.com",
            "service_name": "Haircut",
            "master_name": "Master",
            "datetime": "2024-05-20 10:00",
            "price": 50.0,
            "request_call": False,
        }

        result = await processor.handle_notification(payload)

        assert isinstance(result, UnifiedViewDTO)
        assert result.session_key == 123
        assert result.chat_id == mock_settings.telegram_admin_channel_id
        assert result.message_thread_id == 10

    @pytest.mark.asyncio
    async def test_handle_notification_validation_error(self, mock_settings, mock_container):
        processor = BookingProcessor(mock_settings, mock_container)
        # Missing many required fields
        payload = {"client_name": "Test"}

        result = await processor.handle_notification(payload)
        assert "Error processing notification" in result.content.text
        assert result.session_key == "fail_???"

    @pytest.mark.asyncio
    async def test_handle_status_update_success(self, mock_settings, mock_container):
        processor = BookingProcessor(mock_settings, mock_container)
        appointment_id = 123
        cached_data = {
            "id": appointment_id,
            "client_name": "Test",
            "client_phone": "123",
            "client_email": "t@t.com",
            "service_name": "S",
            "master_name": "M",
            "datetime": "2024",
            "price": 10.0,
            "request_call": False,
            "email_delivery_status": "waiting",
        }
        mock_container.redis.appointment_cache.get.return_value = cached_data

        update_data = {
            "appointment_id": appointment_id,
            "channel": "email",
            "status": "sent",
            "notification_label": "Confirmation",
        }

        result = await processor.handle_status_update(update_data)

        assert result is not None
        assert result.session_key == appointment_id
        # Verify cache was updated
        mock_container.redis.appointment_cache.save.assert_called()

    @pytest.mark.asyncio
    async def test_handle_expire_reschedule(self, mock_settings, mock_container):
        mock_provider = AsyncMock()
        processor = BookingProcessor(mock_settings, mock_container, appointments_provider=mock_provider)

        await processor.handle_expire_reschedule({"appointment_id": "123"})
        mock_provider.expire_reschedule.assert_called_with("123")


class TestContactProcessor:
    @pytest.mark.asyncio
    async def test_handle_notification_success(self, mock_settings, mock_container):
        mock_container.site_settings.aget_field.return_value = "lily_bot"
        processor = ContactProcessor(mock_settings, mock_container)
        payload = {
            "request_id": 1,
            "first_name": "John",
            "contact_value": "555",
            "message": "Hello",
        }

        result = await processor.handle_notification(payload)
        assert result.session_key == "contact_1"
        assert result.message_thread_id == 20


class TestNotificationsOrchestrator:
    @pytest.mark.asyncio
    async def test_delegation(self, mock_settings, mock_container):
        orchestrator = NotificationsOrchestrator(mock_settings, mock_container)
        orchestrator.booking = MagicMock()
        orchestrator.booking.handle_notification = AsyncMock()

        await orchestrator.handle_notification({"id": "1"})
        orchestrator.booking.handle_notification.assert_called_with({"id": "1"})


class TestNotificationHandlers:
    @pytest.mark.asyncio
    async def test_handle_new_appointment_notification(self, mock_container):
        from src.telegram_bot.features.redis.notifications.handlers.handlers import handle_new_appointment_notification

        mock_container.redis_notifications = AsyncMock()
        mock_container.redis_notifications.handle_notification.return_value = UnifiedViewDTO(
            content=ViewResultDTO(text="New booking"), chat_id=1, session_key=1
        )

        message_data = {"id": 123, "event": "booking"}

        await handle_new_appointment_notification(message_data, mock_container)

        mock_container.redis.appointment_cache.save.assert_called_with(123, message_data)
        mock_container.view_sender.send.assert_called()

    @pytest.mark.asyncio
    async def test_handle_status_update_notification(self, mock_container):
        from src.telegram_bot.features.redis.notifications.handlers.handlers import handle_status_update_notification

        mock_container.redis_notifications = AsyncMock()
        mock_container.redis_notifications.handle_status_update.return_value = UnifiedViewDTO(
            content=ViewResultDTO(text="Status update"), chat_id=1, session_key=1
        )

        message_data = {"appointment_id": 123, "status": "sent"}

        await handle_status_update_notification(message_data, mock_container)

        mock_container.redis_notifications.handle_status_update.assert_called_with(message_data)
        mock_container.view_sender.send.assert_called()

    @pytest.mark.asyncio
    async def test_handle_new_contact_request(self, mock_container):
        from src.telegram_bot.features.redis.notifications.handlers.handlers import handle_new_contact_request

        mock_container.redis_notifications = AsyncMock()
        mock_container.redis_notifications.handle_contact_notification.return_value = UnifiedViewDTO(
            content=ViewResultDTO(text="New contact"), chat_id=1, session_key=1
        )

        message_data = {"request_id": 1}

        await handle_new_contact_request(message_data, mock_container)

        mock_container.redis.contact_cache.save.assert_called_with(1, message_data)
        mock_container.view_sender.send.assert_called()

    async def test_handle_delete_notification_callback(self, mock_container, mock_i18n_global):
        from src.telegram_bot.features.redis.notifications.handlers.handlers import handle_delete_notification_callback
        from src.telegram_bot.features.redis.notifications.resources.callbacks import NotificationsCallback

        call = AsyncMock()
        call.message.chat.id = 123
        call.message.message_id = 456
        call.bot.delete_message = AsyncMock()

        callback_data = NotificationsCallback(action="delete_notification", session_id="123", topic_id=None)

        await handle_delete_notification_callback(call, callback_data, mock_container, mock_i18n_global)

        call.bot.delete_message.assert_called_with(chat_id=123, message_id=456)
        mock_container.redis.appointment_cache.delete.assert_called_with("123")
