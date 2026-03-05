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
    Universal task to route notifications to Email, Telegram (Bot), or both.
    """
    try:
        payload = NotificationPayload(**payload_dict)
        log.info(f"Task: universal_notification | ID: {payload.notification_id} | Channels: {payload.channels}")
    except Exception as e:
        log.error(f"Task: universal_notification | Action: ValidationFailed | error={e}")
        return

    notification_service = cast("NotificationService", ctx.get("notification_service"))
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))

    # 1. Handle Email Channel
    if "email" in payload.channels and payload.recipient.email and payload.template_name:
        try:
            subject = payload.subject or "Notification from LILY Salon"
            await notification_service.send_notification(
                email=payload.recipient.email,
                subject=subject,
                template_name=payload.template_name,
                data=payload.context_data,
            )
            log.info(f"Task: universal_notification | Action: EmailSent | ID: {payload.notification_id}")
        except Exception as e:
            log.error(f"Task: universal_notification | Action: EmailFailed | ID: {payload.notification_id} | error={e}")
            # Retry on email failure (network/smtp)
            raise Retry(defer=ctx["job_try"] * 30) from e

    # 2. Handle Telegram Channel
    if "telegram" in payload.channels and payload.event_type and stream_manager:
        try:
            event_data = {
                "type": payload.event_type,
                "notification_id": payload.notification_id,
                **payload.context_data,
            }
            await stream_manager.add_event(RedisStreams.BotEvents.NAME, event_data)
        except Exception as e:
            log.error(
                f"Task: universal_notification | Action: TelegramError | ID: {payload.notification_id} | error={e}"
            )
            raise Retry(defer=ctx["job_try"] * 10) from e


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
        log.error(f"Task: send_group_booking_notification_task | Action: RedisError | error={e}")
        raise Retry(defer=10) from e

    if not raw_data:
        log.error(f"Task: send_group_booking_notification_task | Action: CacheNotFound | key={cache_key}")
        return

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        log.error("Task: send_group_booking_notification_task | Action: JsonParseError")
        return  # Critical code/data error, no retry

    # 2. Send Email
    if data.get("client_email"):
        try:
            await notification_service.send_notification(
                email=data["client_email"],
                subject="Ваша запись в LILY Beauty Salon",
                template_name="bk_group_booking",
                data=data,
            )
            log.info(f"Task: send_group_booking_notification_task | Action: EmailSent | group_id={group_id}")
        except Exception as e:
            log.error(f"Task: send_group_booking_notification_task | Action: EmailFailed | error={e}")
            # Retry on SMTP/Network errors
            raise Retry(defer=ctx["job_try"] * 60) from e


# --- Legacy Tasks ---


async def send_booking_notification_task(ctx: dict[str, Any], appointment_id: int, admin_id: int | None = None) -> None:
    """Legacy task for sending a new booking notification."""
    log.info(
        f"Task: send_booking_notification_task | Action: Start | appointment_id={appointment_id} | try={ctx['job_try']}"
    )

    redis_service = cast("RedisService", ctx.get("redis_service"))
    notification_service = cast("NotificationService", ctx.get("notification_service"))

    cache_key = f"notifications:cache:{appointment_id}"
    raw_data = await redis_service.get_value(cache_key)
    if not raw_data:
        return

    data = json.loads(raw_data)
    if data.get("client_email"):
        try:
            await notification_service.send_notification(
                email=data["client_email"],
                subject="Terminbestätigung - LILY Beauty Salon",
                template_name="bk_new_booking",
                data=data,
            )
        except Exception as e:
            log.error(f"Task: send_booking_notification_task | Action: EmailFailed | error={e}")
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
            await stream_manager.add_event(RedisStreams.BotEvents.NAME, {"type": "contact_request", **data})
        except Exception as e:
            log.error(f"Task: send_contact_notification_task | Action: BotNotifyFailed | error={e}")
            raise Retry(defer=10) from e


async def requeue_event_task(ctx: dict[str, Any], event_data: dict[str, Any]) -> None:
    """Universal task for returning an event to Redis Stream (Retry mechanism)."""
    log.info(f"Task: requeue_event_task | Action: Start | type={event_data.get('type')}")


async def expire_reservation_task(ctx: dict[str, Any], appointment_id: int) -> None:
    """Task for sending an expiration command to the bot."""
    log.info(f"Task: expire_reservation_task | Action: Start | appointment_id={appointment_id}")
