import json
from typing import TYPE_CHECKING, Any, cast

from arq import Retry
from loguru import logger as log

from src.workers.core.streams import RedisStreams
from src.workers.notification_worker.schemas import NotificationPayload
from src.workers.notification_worker.tasks.utils import send_status_update

if TYPE_CHECKING:
    from codex_platform.redis_service import RedisService

    from src.workers.core.streams import StreamManager
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


def _mailbox_headers(context: dict[str, Any]) -> dict[str, str] | None:
    thread_key = context.get("thread_key") or context.get("reply_match_token")
    if not thread_key:
        return None
    clean_key = str(thread_key).strip()
    return {
        "X-Lily-Thread-Key": clean_key,
        "Message-ID": f"<{clean_key}>",
        "References": f"<{clean_key}>",
        "In-Reply-To": f"<{clean_key}>",
    }


def _stream_event_type(event_type: str | None) -> str:
    """Map notification-domain events to bot Redis router event names."""
    if event_type == "booking.received":
        return "new_appointment"
    return str(event_type or "")


def _notification_label(event_type: str | None, template_name: str | None) -> str:
    """Human-readable label for the client notification shown in Telegram."""
    labels = {
        "booking.received": "Заявка получена",
        "booking.confirmed": "Подтверждение записи",
        "booking.cancelled": "Отмена записи",
        "booking.rescheduled": "Предложение переноса",
        "booking.reminder": "Напоминание",
        "booking.no_show": "Неявка",
    }
    if event_type in labels:
        return labels[event_type]

    template_labels = {
        "bk_receipt": "Заявка получена",
        "bk_group_booking": "Заявка получена",
        "bk_confirmation": "Подтверждение записи",
        "bk_cancellation": "Отмена записи",
        "bk_reschedule": "Предложение переноса",
        "bk_reminder": "Напоминание",
        "bk_no_show": "Неявка",
    }
    return template_labels.get(str(template_name or ""), "Письмо клиенту")


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
        headers=_mailbox_headers(payload.context_data),
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
            {"type": _stream_event_type(payload.event_type), **bot_payload},
        )
        log.info(f"Task: universal_notification | Action: StreamSent | event={payload.event_type}")
    except Exception as exc:
        log.error(f"Task: universal_notification | Action: StreamFailed | error={exc}")
        # Intentionally not re-raising: email already sent, retrying would duplicate it.


# ---------------------------------------------------------------------------
# Universal task
# ---------------------------------------------------------------------------


async def send_universal_notification_task(
    ctx: dict[str, Any],
    payload: dict[str, Any] | None = None,
    payload_dict: dict[str, Any] | None = None,
) -> None:
    """
    Universal task to route notifications across email and Telegram channels.
    """
    raw_payload = payload if payload is not None else payload_dict
    if raw_payload is None:
        log.error("Task: universal_notification | Action: MissingPayload")
        return

    try:
        payload_model = NotificationPayload(**raw_payload)
    except Exception as exc:
        log.error(f"Task: universal_notification | Action: ValidationFailed | error={exc}")
        return

    log.info(f"Task: universal_notification | ID: {payload_model.notification_id} | Channels: {payload_model.channels}")

    notification_service = cast("NotificationService", ctx.get("notification_service"))
    stream_manager = cast("StreamManager", ctx.get("stream_manager"))

    # 1. Telegram FIRST — бот должен закешировать данные до прихода notification_status
    if "telegram" in payload_model.channels and payload_model.event_type and stream_manager:
        await _send_to_stream(ctx, payload_model, stream_manager)

    # 2. Email SECOND + status update чтобы бот обновил карточку (✅ письмо отправлено + 🗑)
    if "email" in payload_model.channels and payload_model.recipient.email and payload_model.template_name:
        appointment_id = payload_model.context_data.get("id") or payload_model.context_data.get("group_id")
        try:
            await _send_email(ctx, payload_model, notification_service)
            if appointment_id and stream_manager:
                await send_status_update(
                    ctx,
                    int(appointment_id),
                    "email",
                    "success",
                    event_type=payload_model.event_type,
                    template_name=payload_model.template_name,
                    notification_label=_notification_label(payload_model.event_type, payload_model.template_name),
                )
        except Exception as exc:
            log.error(f"Task: universal_notification | Action: EmailFailed | error={exc}")
            if appointment_id and stream_manager:
                await send_status_update(
                    ctx,
                    int(appointment_id),
                    "email",
                    "failed",
                    event_type=payload_model.event_type,
                    template_name=payload_model.template_name,
                    notification_label=_notification_label(payload_model.event_type, payload_model.template_name),
                )
            raise Retry(defer=ctx["job_try"] * 30) from exc


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
        raw_data = await redis_service.string.get(cache_key)
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
    raw_data = await redis_service.string.get(cache_key)
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
    raw_data = await redis_service.string.get(cache_key)
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
