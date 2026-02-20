from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.shared.core.constants import RedisStreams

if TYPE_CHECKING:
    from src.shared.core.manager_redis.manager import StreamManager
    from src.shared.core.redis_service import RedisService


async def send_booking_notification_task(ctx: dict[str, Any], appointment_id: int, admin_id: int | None = None) -> None:
    """
    Задача для отправки уведомления о новой записи.
    Теперь берет данные из Redis-кеша, подготовленного Django.
    """
    log.info(f"Task: send_booking_notification_task | appointment_id={appointment_id}")

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    redis_service = cast("RedisService", ctx.get("redis_service"))

    if not stream_manager or not redis_service:
        log.error("StreamManager or RedisService not found in context.")
        return

    # Fetch data from Redis
    cache_key = f"notifications:cache:{appointment_id}"
    raw_data = await redis_service.get_value(cache_key)

    if not raw_data:
        log.warning(f"No cache found for appointment {appointment_id}. Skipping notification.")
        return

    try:
        import json

        payload = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

        event_data = payload.copy()
        event_data["type"] = "new_appointment"

        stream_name = RedisStreams.BotEvents.NAME
        message_id = await stream_manager.add_event(stream_name, event_data)

        if message_id:
            log.info(f"Booking notification sent to stream '{stream_name}' | msg_id={message_id}")
        else:
            log.error(f"Failed to send booking notification to stream '{stream_name}'")

    except Exception as e:
        log.exception(f"Error sending booking notification task: {e}")


async def send_contact_notification_task(ctx: dict[str, Any], request_id: int) -> None:
    """
    Задача для отправки уведомления о новой заявке из контактной формы.
    Теперь берет данные из Redis-кеша, подготовленного Django.
    """
    log.info(f"Task: send_contact_notification_task | request_id={request_id}")

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    redis_service = cast("RedisService", ctx.get("redis_service"))

    if not stream_manager or not redis_service:
        log.error("StreamManager or RedisService not found in context.")
        return

    # Fetch data from Redis
    cache_key = f"notifications:contact_cache:{request_id}"
    raw_data = await redis_service.get_value(cache_key)

    if not raw_data:
        log.warning(f"No cache found for contact request {request_id}. Skipping notification.")
        return

    try:
        import json

        payload = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

        event_data = {"type": "new_contact_request", "request_id": str(request_id), **payload}

        stream_name = RedisStreams.BotEvents.NAME
        message_id = await stream_manager.add_event(stream_name, event_data)

        if message_id:
            log.info(f"Contact notification sent to stream '{stream_name}' | msg_id={message_id}")
        else:
            log.error(f"Failed to send contact notification to stream '{stream_name}'")

    except Exception as e:
        log.exception(f"Error sending contact notification task: {e}")


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
