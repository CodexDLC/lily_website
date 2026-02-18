from typing import TYPE_CHECKING, Any, cast

from loguru import logger as log

if TYPE_CHECKING:
    from src.shared.core.manager_redis.manager import StreamManager


async def send_status_update(ctx: dict[str, Any], appointment_id: int | None, channel: str, status: str) -> None:
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
    try:
        await stream_manager.add_event("bot_events", payload)
        log.info(f"Status update sent: {payload}")
    except Exception as e:
        log.error(f"Failed to send status update: {e}")
