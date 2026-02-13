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
        orchestrator = container.notifications
        view_sender = container.view_sender

        log.info(f"Notifications | Processing 'new_appointment' event. ID={message_data.get('id')}")

        # 1. Пытаемся обработать штатно
        try:
            view_dto = orchestrator.handle_notification(message_data)
        except Exception as e:
            log.error(f"Notifications | Orchestrator failed: {e}")
            # 2. Если упало — шлем аварийное уведомление
            view_dto = orchestrator.handle_failure(message_data, str(e))

        # 3. Отправляем (хоть что-то)
        await view_sender.send(view_dto)

    except Exception as e:
        log.critical(f"Notifications | Fatal error in handler: {e}")
