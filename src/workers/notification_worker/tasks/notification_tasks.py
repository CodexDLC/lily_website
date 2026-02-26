from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.shared.core.constants import RedisStreams

if TYPE_CHECKING:
    from src.shared.core.manager_redis.manager import StreamManager
    from src.shared.core.redis_service import RedisService


async def send_booking_notification_task(ctx: dict[str, Any], appointment_id: int, admin_id: int | None = None) -> None:
    """
    Task for sending a new booking notification.
    Fetches data from Redis cache prepared by Django.
    """
    log.info(f"Task: send_booking_notification_task | Action: Start | appointment_id={appointment_id}")

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    redis_service = cast("RedisService", ctx.get("redis_service"))

    if not stream_manager or not redis_service:
        log.error("Task: send_booking_notification_task | Action: Failed | error=ContextMissing")
        return

    # Fetch data from Redis
    cache_key = f"notifications:cache:{appointment_id}"
    log.debug(f"Task: send_booking_notification_task | Action: FetchCache | key={cache_key}")
    raw_data = await redis_service.get_value(cache_key)

    if not raw_data:
        log.warning(
            f"Task: send_booking_notification_task | Action: Skip | reason=NoCacheFound | appointment_id={appointment_id}"
        )
        return

    try:
        import json

        payload = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

        event_data = payload.copy()
        event_data["type"] = "new_appointment"

        stream_name = RedisStreams.BotEvents.NAME
        message_id = await stream_manager.add_event(stream_name, event_data)

        if message_id:
            log.info(
                f"Task: send_booking_notification_task | Action: Success | stream={stream_name} | msg_id={message_id}"
            )
        else:
            log.error(
                f"Task: send_booking_notification_task | Action: Failed | error=StreamAddError | stream={stream_name}"
            )

    except Exception as e:
        log.error(f"Task: send_booking_notification_task | Action: Failed | error={e}")


async def send_contact_notification_task(ctx: dict[str, Any], request_id: int) -> None:
    """
    Task for sending a new contact form notification.
    Fetches data from Redis cache prepared by Django.
    """
    log.info(f"Task: send_contact_notification_task | Action: Start | request_id={request_id}")

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    redis_service = cast("RedisService", ctx.get("redis_service"))

    if not stream_manager or not redis_service:
        log.error("Task: send_contact_notification_task | Action: Failed | error=ContextMissing")
        return

    # Fetch data from Redis
    cache_key = f"notifications:contact_cache:{request_id}"
    log.debug(f"Task: send_contact_notification_task | Action: FetchCache | key={cache_key}")
    raw_data = await redis_service.get_value(cache_key)

    if not raw_data:
        log.warning(
            f"Task: send_contact_notification_task | Action: Skip | reason=NoCacheFound | request_id={request_id}"
        )
        return

    try:
        import json

        payload = json.loads(raw_data) if isinstance(raw_data, str) else raw_data

        event_data = {"type": "new_contact_request", "request_id": str(request_id), **payload}

        stream_name = RedisStreams.BotEvents.NAME
        message_id = await stream_manager.add_event(stream_name, event_data)

        if message_id:
            log.info(
                f"Task: send_contact_notification_task | Action: Success | stream={stream_name} | msg_id={message_id}"
            )
        else:
            log.error(
                f"Task: send_contact_notification_task | Action: Failed | error=StreamAddError | stream={stream_name}"
            )

    except Exception as e:
        log.error(f"Task: send_contact_notification_task | Action: Failed | error={e}")


async def requeue_event_task(ctx: dict[str, Any], event_data: dict[str, Any]) -> None:
    """
    Universal task for returning an event to Redis Stream (Retry mechanism).
    """
    log.info(f"Task: requeue_event_task | Action: Start | type={event_data.get('type')}")

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    if not stream_manager:
        log.error("Task: requeue_event_task | Action: Failed | error=StreamManagerMissing")
        return

    try:
        stream_name = RedisStreams.BotEvents.NAME
        # Increment retry counter
        retries = int(event_data.get("_retries", 0)) + 1
        event_data["_retries"] = str(retries)

        message_id = await stream_manager.add_event(stream_name, event_data)
        log.info(
            f"Task: requeue_event_task | Action: Success | stream={stream_name} | retry={retries} | msg_id={message_id}"
        )

    except Exception as e:
        log.error(f"Task: requeue_event_task | Action: Failed | error={e}")


async def expire_reservation_task(ctx: dict[str, Any], appointment_id: int) -> None:
    """
    Task for sending an expiration command to the bot (triggered 24h after proposal).
    The bot will then call Django API to cancel the pending booking.
    """
    log.info(f"Task: expire_reservation_task | Action: Start | appointment_id={appointment_id}")

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    if not stream_manager:
        log.error("Task: expire_reservation_task | Action: Failed | error=StreamManagerMissing")
        return

    try:
        event_data = {
            "type": "expire_reschedule",
            "appointment_id": appointment_id,
        }

        stream_name = RedisStreams.BotEvents.NAME
        message_id = await stream_manager.add_event(stream_name, event_data)

        if message_id:
            log.info(f"Task: expire_reservation_task | Action: Success | stream={stream_name} | msg_id={message_id}")
        else:
            log.error(f"Task: expire_reservation_task | Action: Failed | error=StreamAddError | stream={stream_name}")

    except Exception as e:
        log.error(f"Task: expire_reservation_task | Action: Failed | error={e}")
