from typing import Any

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery
from codex_bot.redis import RedisRouter
from loguru import logger as log

from src.telegram_bot.features.redis.notifications.resources.callbacks import NotificationsCallback

# Создаем роутер для уведомлений
notifications_router = RedisRouter()
router = Router(name="redis_notifications_router")


async def _clear_deleted_notification_state(
    callback_data: NotificationsCallback,
    container: Any,
    chat_id: int | str,
    thread_id: int | None,
) -> None:
    session_id = callback_data.session_id
    if session_id is not None:
        session_key = str(session_id)
        try:
            if session_key.startswith("contact_"):
                await container.redis.contact_cache.delete(session_key.removeprefix("contact_"))
            else:
                await container.redis.appointment_cache.delete(session_key)
        except Exception as e:
            log.warning(f"Notifications | Delete callback cache cleanup failed: {e}")

    sender_key = f"{chat_id}:{thread_id}" if thread_id else str(chat_id)
    try:
        await container.redis.sender.clear_coords(sender_key, is_channel=True)
    except Exception as e:
        log.warning(f"Notifications | Delete callback sender cleanup failed: {e}")


@router.callback_query(NotificationsCallback.filter(F.action == "delete_notification"))
async def handle_delete_notification_callback(
    call: CallbackQuery,
    callback_data: NotificationsCallback,
    container: Any,
) -> None:
    """
    Handles inline "Удалить" buttons produced by Redis notification cards.
    """
    message = call.message
    if not message:
        await call.answer("Сообщение недоступно.", show_alert=True)
        return

    chat = getattr(message, "chat", None)
    message_id = getattr(message, "message_id", None)
    if not chat or not message_id:
        await call.answer("Сообщение недоступно.", show_alert=True)
        return

    chat_id = chat.id
    thread_id = getattr(message, "message_thread_id", None) or callback_data.topic_id

    if not call.bot:
        log.error("Notifications | Callback error: bot instance is None")
        return

    try:
        await call.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramAPIError as e:
        log.warning(
            "Notifications | Delete callback failed | "
            f"chat_id={chat_id} message_id={message_id} session_id={callback_data.session_id} error={e}"
        )
        await call.answer("Не удалось удалить сообщение.", show_alert=True)
        return

    await _clear_deleted_notification_state(callback_data, container, chat_id=chat_id, thread_id=thread_id)
    await call.answer("Удалено")


@notifications_router.message("new_appointment")
async def handle_new_appointment_notification(message_data: dict[str, Any], container: Any):
    """
    Хендлер для нового уведомления о записи.
    """
    try:
        orchestrator = container.redis_notifications
        view_sender = container.view_sender
        cache_manager = container.redis.appointment_cache

        appointment_id = message_data.get("id")
        log.info(f"Notifications | Processing 'new_appointment' event. ID={appointment_id}")

        # 1. Сохраняем данные в кэш Redis для последующего использования в UI-фиче
        if appointment_id:
            await cache_manager.save(appointment_id, message_data)
            log.debug(f"Notifications | Appointment {appointment_id} cached in Redis.")

        # 2. Пытаемся обработать штатно (формируем UnifiedViewDTO)
        try:
            view_dto = await orchestrator.handle_notification(message_data)
        except Exception as e:
            log.error(f"Notifications | Orchestrator failed: {e}")
            # 3. Если упало — шлем аварийное уведомление
            view_dto = await orchestrator.handle_failure(message_data, str(e))

        # 4. Отправляем уведомление в Telegram
        await view_sender.send(view_dto)

    except Exception as e:
        log.critical(f"Notifications | Fatal error in handler: {e}")


@notifications_router.message("notification_status")
async def handle_status_update_notification(message_data: dict[str, Any], container: Any):
    """
    Хендлер для обновления статуса отправки (Email/SMS).
    """
    try:
        orchestrator = container.redis_notifications
        view_sender = container.view_sender

        appointment_id = message_data.get("appointment_id") or message_data.get("confirmation_id")
        log.info(f"Notifications | Processing 'notification_status' event. ID={appointment_id}")

        if not appointment_id:
            log.warning("Notifications | No appointment_id in status update.")
            return

        # 1. Вызываем оркестратор (он сам восстановит текст из кэша)
        try:
            view_dto = await orchestrator.handle_status_update(message_data)
        except Exception as e:
            log.error(f"Notifications | Orchestrator handle_status_update failed: {e}")
            return

        if not view_dto:
            log.debug("Notifications | Status update yielded no changes (DTO is None).")
            return

        # 2. Отправляем обновление в Telegram
        await view_sender.send(view_dto)

    except Exception as e:
        log.critical(f"Notifications | Fatal error in status handler: {e}")


@notifications_router.message("new_contact_request")
async def handle_new_contact_request(message_data: dict[str, Any], container: Any):
    """
    Хендлер для нового уведомления из контактной формы.
    """
    try:
        orchestrator = container.redis_notifications
        view_sender = container.view_sender
        contact_cache = container.redis.contact_cache

        request_id = message_data.get("request_id")
        log.info(f"Notifications | Processing 'new_contact_request' event. ID={request_id}")

        # 1. Сохраняем данные в кэш Redis для последующего использования (кнопка «Прочитать»)
        if request_id:
            await contact_cache.save(request_id, message_data)
            log.debug(f"Notifications | Contact request {request_id} cached in Redis.")

        # 2. Формируем превью-уведомление (короткий текст + кнопка "Открыть бота")
        try:
            view_dto = await orchestrator.handle_contact_notification(message_data)
        except Exception as e:
            log.error(f"Notifications | Contact orchestrator failed: {e}")
            view_dto = orchestrator.contact.handle_failure(message_data, str(e))

        # 3. Отправляем уведомление в Telegram
        await view_sender.send(view_dto)

    except Exception as e:
        log.critical(f"Notifications | Fatal error in contact handler: {e}")


@notifications_router.message("expire_reschedule")
async def handle_expire_reschedule(message_data: dict[str, Any], container: Any):
    """
    Хендлер для события "истекло время на подтверждение переноса записи".
    Делегирует работу оркестратору, который отправляет API запрос в Django.
    """
    try:
        orchestrator = container.redis_notifications

        appointment_id = message_data.get("appointment_id")
        log.info(f"Notifications | Processing 'expire_reschedule' event. ID={appointment_id}")

        if not appointment_id:
            log.warning("Notifications | No appointment_id in expire_reschedule.")
            return

        try:
            await orchestrator.handle_expire_reschedule(message_data)
        except Exception as e:
            log.error(f"Notifications | Orchestrator handle_expire_reschedule failed: {e}")

    except Exception as e:
        log.critical(f"Notifications | Fatal error in expire_reschedule handler: {e}")
