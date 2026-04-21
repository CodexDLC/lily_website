from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.telegram_bot.features.redis.notifications.handlers.handlers import handle_delete_notification_callback
from src.telegram_bot.features.redis.notifications.resources.callbacks import NotificationsCallback


def _make_call(chat_id: int = -100123, message_id: int = 42, thread_id: int | None = 7):
    return SimpleNamespace(
        message=SimpleNamespace(
            chat=SimpleNamespace(id=chat_id),
            message_id=message_id,
            message_thread_id=thread_id,
        ),
        bot=SimpleNamespace(delete_message=AsyncMock()),
        answer=AsyncMock(),
    )


def _make_container():
    return SimpleNamespace(
        redis=SimpleNamespace(
            sender=SimpleNamespace(clear_coords=AsyncMock()),
            appointment_cache=SimpleNamespace(delete=AsyncMock()),
            contact_cache=SimpleNamespace(delete=AsyncMock()),
        )
    )


@pytest.mark.asyncio
async def test_delete_notification_callback_deletes_booking_message_and_state():
    call = _make_call()
    container = _make_container()
    callback_data = NotificationsCallback(action="delete_notification", session_id=123, topic_id=7)

    await handle_delete_notification_callback(call, callback_data, container)

    call.bot.delete_message.assert_awaited_once_with(chat_id=-100123, message_id=42)
    container.redis.appointment_cache.delete.assert_awaited_once_with("123")
    container.redis.contact_cache.delete.assert_not_awaited()
    container.redis.sender.clear_coords.assert_awaited_once_with("-100123:7", is_channel=True)
    call.answer.assert_awaited_once_with("Удалено")


@pytest.mark.asyncio
async def test_delete_notification_callback_clears_contact_cache():
    call = _make_call(thread_id=11)
    container = _make_container()
    callback_data = NotificationsCallback(action="delete_notification", session_id="contact_55", topic_id=None)

    await handle_delete_notification_callback(call, callback_data, container)

    container.redis.contact_cache.delete.assert_awaited_once_with("55")
    container.redis.appointment_cache.delete.assert_not_awaited()
    container.redis.sender.clear_coords.assert_awaited_once_with("-100123:11", is_channel=True)
