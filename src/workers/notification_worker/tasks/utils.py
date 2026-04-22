from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

from src.workers.core.streams import RedisStreams

if TYPE_CHECKING:
    from src.workers.core.streams import StreamManager


async def send_status_update(
    ctx: dict[str, Any],
    appointment_id: int | None,
    channel: str,
    status: str,
    *,
    event_type: str | None = None,
    template_name: str | None = None,
    notification_label: str | None = None,
) -> None:
    """
    Отправка статуса отправки уведомления обратно в Redis Stream.
    Используется задачами Twilio и Email для обновления UI в боте.
    """
    if not appointment_id:
        return

    stream_manager = cast("StreamManager | None", ctx.get("stream_manager"))
    if not stream_manager:
        log.warning("StreamManager not available for status update.")
        return

    payload = {
        "type": "notification_status",
        "appointment_id": appointment_id,
        "channel": channel,
        "status": status,
    }
    if event_type:
        payload["event_type"] = event_type
    if template_name:
        payload["template_name"] = template_name
    if notification_label:
        payload["notification_label"] = notification_label
    try:
        await stream_manager.add_event(RedisStreams.BotEvents.NAME, payload)
        log.info(f"Status update sent: {payload}")
    except Exception as e:
        log.error(f"Failed to send status update: {e}")
