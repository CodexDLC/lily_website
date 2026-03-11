import json
from typing import TYPE_CHECKING, Any, cast

from arq import Retry
from loguru import logger as log

from src.shared.core.constants import RedisStreams
from src.workers.notification_worker.schemas import NotificationPayload

if TYPE_CHECKING:
    from src.shared.core.manager_redis.manager import StreamManager
    from src.shared.core.redis_service import RedisService
    from src.workers.notification_worker.services.notification_service import NotificationService


async def send_universal_notification_task(ctx: dict[str, Any], payload_dict: dict[str, Any]) -> None:
    """
    Universal task to route notifications.
    """
    try:
        payload = NotificationPayload(**payload_dict)
        log.info(f"Task: universal_notification | ID: {payload.notification_id} | Channels: {payload.channels}")
    except Exception as e:
        log.error(f"Task: universal_notification | Action: ValidationFailed | error={e}")
        return

    notification_service = cast("NotificationService", ctx.get("notification_service"))
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))

    # For universal task, we still use the service's logic but respect the requested channels
    # 1. Email Channel
    if "email" in payload.channels and payload.recipient.email and payload.template_name:
        try:
            await notification_service.send_notification(
                email=payload.recipient.email,
                subject=payload.subject or "Notification from LILY Salon",
                template_name=payload.template_name,
                data=payload.context_data,
            )
        except Exception as e:
            log.error(f"Task: universal_notification | Action: EmailFailed | error={e}")
            raise Retry(defer=ctx["job_try"] * 30) from e

    # 2. Telegram Channel (Notify Bot via Redis Stream)
    if "telegram" in payload.channels and payload.event_type and stream_manager:
        try:
            # Reconstruct bot payload from context_data or recipient
            bot_payload = payload.context_data.copy()

            # Handle Group Bookings (multiple items)
            items = bot_payload.get("items", [])
            if items and isinstance(items, list):
                if "service_name" not in bot_payload:
                    bot_payload["service_name"] = ", ".join([str(i.get("service_name", "")) for i in items])
                if "master_name" not in bot_payload:
                    # Unique masters
                    masters = list(dict.fromkeys([str(i.get("master_name", "")) for i in items]))
                    bot_payload["master_name"] = ", ".join(masters)
                if "price" not in bot_payload:
                    bot_payload["price"] = bot_payload.get("total_price", 0.0)
                if "datetime" not in bot_payload:
                    # Use booking_date if available
                    bot_payload["datetime"] = bot_payload.get("booking_date", "")

            # Ensure basic fields are present if not in context_data
            if "id" not in bot_payload:
                bot_payload["id"] = bot_payload.get("group_id") or payload.notification_id
            if "client_name" not in bot_payload:
                bot_payload["client_name"] = f"{payload.recipient.first_name} {payload.recipient.last_name}".strip()
            if "first_name" not in bot_payload:
                bot_payload["first_name"] = payload.recipient.first_name
            if "last_name" not in bot_payload:
                bot_payload["last_name"] = payload.recipient.last_name
            if "client_phone" not in bot_payload:
                bot_payload["client_phone"] = payload.recipient.phone
            if "client_email" not in bot_payload:
                bot_payload["client_email"] = payload.recipient.email

            # Ensure required fields for Pydantic validation (in case they are still missing)
            if "service_name" not in bot_payload:
                bot_payload["service_name"] = "N/A"
            if "master_name" not in bot_payload:
                bot_payload["master_name"] = "N/A"
            if "price" not in bot_payload:
                bot_payload["price"] = 0.0
            if "datetime" not in bot_payload:
                bot_payload["datetime"] = "N/A"
            if "request_call" not in bot_payload:
                bot_payload["request_call"] = False

            # Ensure all values are strings for Redis Stream
            bot_payload = {k: str(v) if v is not None else "" for k, v in bot_payload.items() if k != "items"}

            await stream_manager.add_event(
                RedisStreams.BotEvents.NAME, {"type": str(payload.event_type), **bot_payload}
            )
            log.info(f"Task: universal_notification | Action: StreamSent | event={payload.event_type}")
        except Exception as e:
            log.error(f"Task: universal_notification | Action: StreamFailed | error={e}")
            # We don't necessarily want to retry only because of stream failure if email worked,
            # but usually, we want both. For now, just log the error.


async def send_group_booking_notification_task(ctx: dict[str, Any], group_id: int) -> None:
    """
    Task for sending a unified notification for a group of appointments.
    """
    log.info(f"Task: send_group_booking_notification_task | Action: Start | group_id={group_id} | try={ctx['job_try']}")

    redis_service = cast("RedisService", ctx.get("redis_service"))
    notification_service = cast("NotificationService", ctx.get("notification_service"))

    # 1. Fetch data from Redis
    cache_key = f"notifications:group_cache:{group_id}"
    try:
        raw_data = await redis_service.get_value(cache_key)
    except Exception as e:
        raise Retry(defer=10) from e

    if not raw_data:
        log.error(f"Task: send_group_booking_notification_task | Action: CacheNotFound | key={cache_key}")
        return

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return

    # 2. Notify Telegram bot via Redis Stream
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    if stream_manager:
        items = data.get("items", [])
        bot_payload = {
            "id": data["group_id"],
            "client_name": data.get("client_name", ""),
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "client_phone": data.get("client_phone", ""),
            "client_email": data.get("client_email", ""),
            "service_name": f"Gruppe ({len(items)})",
            "master_name": items[0]["master_name"] if items else "",
            "datetime": data.get("booking_date", ""),
            "duration_minutes": data.get("total_duration", 0),
            "price": data.get("total_price", 0.0),
            "request_call": False,
        }
        try:
            await stream_manager.add_event(RedisStreams.BotEvents.NAME, {"type": "new_appointment", **bot_payload})
            log.info(f"Task: send_group_booking_notification_task | Action: StreamSent | group_id={group_id}")
        except Exception as e:
            log.error(f"Task: send_group_booking_notification_task | Action: StreamFailed | error={e}")

    # 3. Send via Service (Service handles Email -> SendGrid fallback)
    if data.get("client_email"):
        try:
            await notification_service.send_notification(
                email=data["client_email"],
                subject="Ваша запись в LILY Beauty Salon",
                template_name="bk_group_booking",
                data=data,
            )
        except Exception as e:
            raise Retry(defer=ctx["job_try"] * 60) from e


# --- Legacy Tasks ---


async def send_booking_notification_task(ctx: dict[str, Any], appointment_id: int, admin_id: int | None = None) -> None:
    """Legacy task for sending a new booking notification."""
    log.info(
        f"Task: send_booking_notification_task | Action: Start | appointment_id={appointment_id} | try={ctx['job_try']}"
    )

    redis_service = cast("RedisService", ctx.get("redis_service"))
    notification_service = cast("NotificationService", ctx.get("notification_service"))
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))

    cache_key = f"notifications:cache:{appointment_id}"
    raw_data = await redis_service.get_value(cache_key)
    if not raw_data:
        return

    data = json.loads(raw_data)

    if stream_manager:
        try:
            await stream_manager.add_event(RedisStreams.BotEvents.NAME, {"type": "new_appointment", **data})
            log.info(f"Task: send_booking_notification_task | Action: StreamSent | appointment_id={appointment_id}")
        except Exception as e:
            log.error(f"Task: send_booking_notification_task | Action: StreamFailed | error={e}")

    if data.get("client_email"):
        try:
            await notification_service.send_notification(
                email=data["client_email"],
                subject="Buchungsanfrage erhalten - LILY Beauty Salon",
                template_name="bk_receipt",
                data=data,
            )
        except Exception as e:
            raise Retry(defer=ctx["job_try"] * 60) from e


async def send_contact_notification_task(ctx: dict[str, Any], request_id: int) -> None:
    """Legacy task for sending a new contact form notification."""
    log.info(f"Task: send_contact_notification_task | Action: Start | request_id={request_id}")

    redis_service = cast("RedisService", ctx.get("redis_service"))
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))

    cache_key = f"notifications:contact_cache:{request_id}"
    raw_data = await redis_service.get_value(cache_key)
    if not raw_data:
        return

    data = json.loads(raw_data)
    if stream_manager:
        try:
            await stream_manager.add_event(RedisStreams.BotEvents.NAME, {"type": "new_contact_request", **data})
        except Exception as e:
            raise Retry(defer=10) from e


async def requeue_event_task(ctx: dict[str, Any], event_data: dict[str, Any]) -> None:
    """Universal task for returning an event to Redis Stream (Retry mechanism)."""
    log.info(f"Task: requeue_event_task | Action: Start | type={event_data.get('type')}")


async def expire_reservation_task(ctx: dict[str, Any], appointment_id: int) -> None:
    """Task for sending an expiration command to the bot."""
    log.info(f"Task: expire_reservation_task | Action: Start | appointment_id={appointment_id}")
