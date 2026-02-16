from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.shared.core.constants import RedisStreams

if TYPE_CHECKING:
    from src.shared.core.manager_redis.manager import StreamManager


async def send_booking_notification_task(
    ctx: dict[str, Any], appointment_data: dict[str, Any], admin_id: int | None = None
) -> None:
    """
    Задача для отправки уведомления о новой записи.
    """
    log.info(f"Task: send_booking_notification_task | appointment_id={appointment_data.get('id')}")

    # Use cast to satisfy Mypy
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    if not stream_manager:
        log.error("StreamManager not found in context. Cannot send notification.")
        return

    event_data = appointment_data.copy()
    event_data["type"] = "new_appointment"

    try:
        stream_name = RedisStreams.BotEvents.NAME
        message_id = await stream_manager.add_event(stream_name, event_data)

        if message_id:
            log.info(f"Notification sent to stream '{stream_name}' | msg_id={message_id}")
        else:
            log.error(f"Failed to send notification to stream '{stream_name}'")

    except Exception as e:
        log.exception(f"Error sending notification task: {e}")


async def requeue_event_task(ctx: dict[str, Any], event_data: dict[str, Any]) -> None:
    """
    Универсальная задача для возврата события в Redis Stream (Retry mechanism).
    """
    log.info(f"Task: requeue_event_task | type={event_data.get('type')}")

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    if not stream_manager:
        log.error("StreamManager not found in context.")
        return

    try:
        stream_name = RedisStreams.BotEvents.NAME
        # Увеличиваем счетчик попыток
        retries = int(event_data.get("_retries", 0)) + 1
        event_data["_retries"] = str(retries)

        message_id = await stream_manager.add_event(stream_name, event_data)
        log.info(f"Event requeued to '{stream_name}' | retry={retries} | msg_id={message_id}")

    except Exception as e:
        log.error(f"Failed to requeue event: {e}")
