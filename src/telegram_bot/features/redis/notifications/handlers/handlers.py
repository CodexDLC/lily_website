from typing import Any

from loguru import logger as log

from src.telegram_bot.services.redis.router import RedisRouter

# Создаем роутер для уведомлений
notifications_router = RedisRouter()


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
            view_dto = orchestrator.handle_notification(message_data)
        except Exception as e:
            log.error(f"Notifications | Orchestrator failed: {e}")
            # 3. Если упало — шлем аварийное уведомление
            view_dto = orchestrator.handle_failure(message_data, str(e))

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
