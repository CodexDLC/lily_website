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
