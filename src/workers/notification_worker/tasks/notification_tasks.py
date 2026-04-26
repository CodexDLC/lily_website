import json
from typing import TYPE_CHECKING, Any, cast

from arq import Retry
from loguru import logger as log

from src.workers.notification_worker.schemas import NotificationPayload

if TYPE_CHECKING:
    from codex_platform.redis_service import RedisService

    from src.workers.notification_worker.services.notification_service import NotificationService

_CAMPAIGN_MAX_TRIES = 5


async def _report_campaign_status(
    ctx: dict[str, Any],
    notification_id: str,
    status: str,
    error: str = "",
) -> None:
    if not notification_id.startswith("campaign_"):
        return
    internal_api = ctx.get("internal_api")
    if not internal_api:
        return
    from src.workers.core.config import WorkerSettings

    settings = WorkerSettings()
    token = settings.ops_worker_api_key
    if not token:
        log.warning("_report_campaign_status: CAMPAIGNS_WORKER_API_KEY not set, skipping callback")
        return
    try:
        await internal_api.post(
            "/v1/conversations/campaigns/recipient-status",
            scope="campaigns.worker",
            token=token,
            json={"notification_id": notification_id, "status": status, "error": error},
        )
    except Exception as exc:
        log.warning(f"_report_campaign_status: callback failed for {notification_id}: {exc}")


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
    raw_payload: dict[str, Any],
) -> None:
    """Sends the email channel. Raises Retry on failure."""
    mode = getattr(payload, "mode", raw_payload.get("mode", "template"))
    html_content = getattr(payload, "html_content", raw_payload.get("html_content"))

    if mode == "rendered" and html_content:
        await notification_service.send_rendered_notification(
            email=payload.recipient.email,  # type: ignore[arg-type]
            subject=payload.subject or raw_payload.get("subject") or "Notification from LILY Salon",
            html_content=html_content,
            headers=_mailbox_headers(payload.context_data),
        )
    elif payload.template_name:
        await notification_service.send_notification(
            email=payload.recipient.email,  # type: ignore[arg-type]
            subject=payload.subject or "Notification from LILY Salon",
            template_name=payload.template_name,
            data=payload.context_data,
            headers=_mailbox_headers(payload.context_data),
        )


async def _send_to_stream(
    ctx: dict[str, Any],
    payload: NotificationPayload,
) -> None:
    """
    Sends the Telegram channel via Redis Stream.

    Telegram notification is secondary: failures are logged but never cause
    a task retry — doing so would resend the already-delivered email.
    """
    try:
        log.debug("Telegram bot notifications are disabled. Skipping stream write.")
    except Exception as exc:
        log.error(f"Task: universal_notification | Action: StreamFailed | error={exc}")


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

    # Defensive extraction in case of partial worker reloads
    mode = getattr(payload_model, "mode", raw_payload.get("mode", "template"))
    html_content = getattr(payload_model, "html_content", raw_payload.get("html_content"))

    should_send_email = (
        "email" in payload_model.channels
        and payload_model.recipient.email
        and (payload_model.template_name or (mode == "rendered" and html_content))
    )

    if should_send_email:
        try:
            await _send_email(ctx, payload_model, notification_service, raw_payload)
            await _report_campaign_status(ctx, payload_model.notification_id, "sent")
        except Exception as exc:
            log.error(f"Task: universal_notification | Action: EmailFailed | error={exc}")
            job_try = ctx.get("job_try", 1)
            if job_try >= _CAMPAIGN_MAX_TRIES:
                await _report_campaign_status(ctx, payload_model.notification_id, "failed", error=str(exc))
                return
            raise Retry(defer=job_try * 30) from exc


async def send_rendered_notification_task(
    ctx: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    """
    Task for sending pre-rendered HTML emails.
    Payload expected keys: 'email', 'subject', 'html_content', 'headers' (optional).
    """
    email = payload.get("email")
    subject = payload.get("subject", "Notification from LILY Salon")
    html_content = payload.get("html_content")
    headers = payload.get("headers")

    if not email or not html_content:
        log.error(f"Task: send_rendered_notification_task | Action: MissingFields | email={email}")
        return

    log.info(f"Task: send_rendered_notification_task | Action: Send | to={email}")
    notification_service = cast("NotificationService", ctx.get("notification_service"))

    try:
        await notification_service.send_rendered_notification(
            email=email,
            subject=subject,
            html_content=html_content,
            headers=headers,
        )
    except Exception as exc:
        log.error(f"Task: send_rendered_notification_task | Action: Failed | error={exc}")
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

    # Stream writing to bot has been disabled
    log.debug(f"Task: send_group_booking_notification_task | Action: StreamDisabled | group_id={group_id}")

    if data.get("client_email"):
        try:
            await notification_service.send_notification(
                email=data["client_email"],
                subject="Eingangsbestätigung: Ihre Terminanfrage | LILY Beauty",
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

    cache_key = f"notifications:cache:{appointment_id}"
    raw_data = await redis_service.string.get(cache_key)
    if not raw_data:
        return

    data = json.loads(raw_data)

    # Stream writing to bot has been disabled
    log.debug(f"Task: send_booking_notification_task | Action: StreamDisabled | appointment_id={appointment_id}")

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

    cache_key = f"notifications:contact_cache:{request_id}"
    raw_data = await redis_service.string.get(cache_key)
    if not raw_data:
        return

    # Stream writing to bot has been disabled
    log.debug(f"Task: send_contact_notification_task | Action: StreamDisabled | request_id={request_id}")


async def requeue_event_task(ctx: dict[str, Any], event_data: dict[str, Any]) -> None:
    """Universal task for returning an event to Redis Stream (Retry mechanism)."""
    log.info(f"Task: requeue_event_task | Action: Start | type={event_data.get('type')}")


async def expire_reservation_task(ctx: dict[str, Any], appointment_id: int) -> None:
    """Task for sending an expiration command to the bot."""
    log.info(f"Task: expire_reservation_task | Action: Start | appointment_id={appointment_id}")
