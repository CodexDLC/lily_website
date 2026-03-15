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


# ---------------------------------------------------------------------------
# BotPayloadEnricher
# Responsible for building the Redis Stream payload dict from a
# NotificationPayload. Keeps business-logic mapping out of the task layer.
# ---------------------------------------------------------------------------


class BotPayloadEnricher:
    """
    Transforms a validated ``NotificationPayload`` into a flat ``dict[str, str]``
    ready to be written to the Redis Stream.

    All missing fields are filled with sensible defaults; nested objects
    (e.g. group booking items) are flattened into scalar strings.
    """

    @staticmethod
    def enrich(payload: NotificationPayload) -> dict[str, str]:
        bot: dict[str, Any] = payload.context_data.copy()

        # --- Group booking: flatten items list into scalar fields ---
        items: list[dict] = bot.get("items", [])
        if items and isinstance(items, list):
            if "service_name" not in bot:
                bot["service_name"] = ", ".join(str(i.get("service_name", "")) for i in items)
            if "master_name" not in bot:
                masters = list(dict.fromkeys(str(i.get("master_name", "")) for i in items))
                bot["master_name"] = ", ".join(masters)
            if "price" not in bot:
                bot["price"] = bot.get("total_price", 0.0)
            if "datetime" not in bot:
                bot["datetime"] = bot.get("booking_date", "")

        # --- Required identification fields ---
        if "id" not in bot:
            bot["id"] = bot.get("group_id") or payload.notification_id
        if "client_name" not in bot:
            bot["client_name"] = f"{payload.recipient.first_name} {payload.recipient.last_name}".strip()
        if "first_name" not in bot:
            bot["first_name"] = payload.recipient.first_name
        if "last_name" not in bot:
            bot["last_name"] = payload.recipient.last_name
        if "client_phone" not in bot:
            bot["client_phone"] = payload.recipient.phone
        if "client_email" not in bot:
            bot["client_email"] = payload.recipient.email

        # --- Pydantic-validated field defaults ---
        bot.setdefault("service_name", "N/A")
        bot.setdefault("master_name", "N/A")
        bot.setdefault("price", 0.0)
        bot.setdefault("datetime", "N/A")
        bot.setdefault("request_call", False)

        # Flatten to str; drop the already-processed items list
        return {k: str(v) if v is not None else "" for k, v in bot.items() if k != "items"}


# ---------------------------------------------------------------------------
# Private channel helpers
# ---------------------------------------------------------------------------


async def _send_email(
    ctx: dict[str, Any],
    payload: NotificationPayload,
    notification_service: "NotificationService",
) -> None:
    """Sends the email channel. Raises Retry on failure (primary channel)."""
    await notification_service.send_notification(
        email=payload.recipient.email,  # type: ignore[arg-type]
        subject=payload.subject or "Notification from LILY Salon",
        template_name=payload.template_name,  # type: ignore[arg-type]
        data=payload.context_data,
    )


async def _send_to_stream(
    ctx: dict[str, Any],
    payload: NotificationPayload,
    stream_manager: "StreamManager",
) -> None:
    """
    Sends the Telegram channel via Redis Stream.

    Telegram notification is secondary: failures are logged but never cause
    a task retry — doing so would resend the already-delivered email.
    """
    try:
        bot_payload = BotPayloadEnricher.enrich(payload)
        await stream_manager.add_event(
            RedisStreams.BotEvents.NAME,
            {"type": str(payload.event_type), **bot_payload},
        )
        log.info(f"Task: universal_notification | Action: StreamSent | event={payload.event_type}")
    except Exception as exc:
        log.error(f"Task: universal_notification | Action: StreamFailed | error={exc}")
        # Intentionally not re-raising: email already sent, retrying would duplicate it.


# ---------------------------------------------------------------------------
# Universal task
# ---------------------------------------------------------------------------


async def send_universal_notification_task(ctx: dict[str, Any], payload_dict: dict[str, Any]) -> None:
    """
    Universal task to route notifications across email and Telegram channels.
    """
    try:
        payload = NotificationPayload(**payload_dict)
    except Exception as exc:
        log.error(f"Task: universal_notification | Action: ValidationFailed | error={exc}")
        return

    log.info(f"Task: universal_notification | ID: {payload.notification_id} | Channels: {payload.channels}")

    notification_service = cast("NotificationService", ctx.get("notification_service"))
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))

    if "email" in payload.channels and payload.recipient.email and payload.template_name:
        try:
            await _send_email(ctx, payload, notification_service)
        except Exception as exc:
            log.error(f"Task: universal_notification | Action: EmailFailed | error={exc}")
            raise Retry(defer=ctx["job_try"] * 30) from exc

    if "telegram" in payload.channels and payload.event_type and stream_manager:
        await _send_to_stream(ctx, payload, stream_manager)


# ---------------------------------------------------------------------------
# Group booking task
# ---------------------------------------------------------------------------


async def send_group_booking_notification_task(ctx: dict[str, Any], group_id: int) -> None:
    """
    Task for sending a unified notification for a group of appointments.
    """
    log.info(f"Task: send_group_booking_notification_task | Action: Start | group_id={group_id} | try={ctx['job_try']}")

    redis_service = cast("RedisService", ctx.get("redis_service"))
    notification_service = cast("NotificationService", ctx.get("notification_service"))

    cache_key = f"notifications:group_cache:{group_id}"
    try:
        raw_data = await redis_service.get_value(cache_key)
    except Exception as exc:
        raise Retry(defer=10) from exc

    if not raw_data:
        log.error(f"Task: send_group_booking_notification_task | Action: CacheNotFound | key={cache_key}")
        return

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        log.error(f"Task: send_group_booking_notification_task | Action: JSONDecodeError | key={cache_key}")
        return

    stream_manager = cast("StreamManager", ctx.get("stream_manager"))
    if stream_manager:
        items: list[dict] = data.get("items", [])
        bot_payload: dict[str, str] = {
            "id": str(data["group_id"]),
            "client_name": str(data.get("client_name", "")),
            "first_name": str(data.get("first_name", "")),
            "last_name": str(data.get("last_name", "")),
            "client_phone": str(data.get("client_phone", "")),
            "client_email": str(data.get("client_email", "")),
            "service_name": f"Gruppe ({len(items)})",
            "master_name": str(items[0]["master_name"]) if items else "",
            "datetime": str(data.get("booking_date", "")),
            "duration_minutes": str(data.get("total_duration", 0)),
            "price": str(data.get("total_price", 0.0)),
            "request_call": "False",
        }
        try:
            await stream_manager.add_event(RedisStreams.BotEvents.NAME, {"type": "new_appointment", **bot_payload})
            log.info(f"Task: send_group_booking_notification_task | Action: StreamSent | group_id={group_id}")
        except Exception as exc:
            log.error(f"Task: send_group_booking_notification_task | Action: StreamFailed | error={exc}")

    if data.get("client_email"):
        try:
            await notification_service.send_notification(
                email=data["client_email"],
                subject="Ваша запись в LILY Beauty Salon",
                template_name="bk_group_booking",
                data=data,
            )
        except Exception as exc:
            raise Retry(defer=ctx["job_try"] * 60) from exc


# ---------------------------------------------------------------------------
# Legacy tasks
# ---------------------------------------------------------------------------


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
        except Exception as exc:
            log.error(f"Task: send_booking_notification_task | Action: StreamFailed | error={exc}")

    if data.get("client_email"):
        try:
            await notification_service.send_notification(
                email=data["client_email"],
                subject="Buchungsanfrage erhalten - LILY Beauty Salon",
                template_name="bk_receipt",
                data=data,
            )
        except Exception as exc:
            raise Retry(defer=ctx["job_try"] * 60) from exc


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
        except Exception as exc:
            raise Retry(defer=10) from exc


async def requeue_event_task(ctx: dict[str, Any], event_data: dict[str, Any]) -> None:
    """Universal task for returning an event to Redis Stream (Retry mechanism)."""
    log.info(f"Task: requeue_event_task | Action: Start | type={event_data.get('type')}")


async def expire_reservation_task(ctx: dict[str, Any], appointment_id: int) -> None:
    """Task for sending an expiration command to the bot."""
    log.info(f"Task: expire_reservation_task | Action: Start | appointment_id={appointment_id}")
