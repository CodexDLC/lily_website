from typing import TYPE_CHECKING, Any

from codex_bot.base import UnifiedViewDTO, ViewResultDTO
from loguru import logger as log

from src.telegram_bot.core.config import BotSettings

from ..resources.formatters import format_contact_preview
from ..resources.keyboards import build_contact_preview_kb

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class ContactProcessor:
    """
    Processor for handling contact form notifications.
    Sends a preview message with an "Open Bot" button to the main channel (General).
    """

    def __init__(self, settings: BotSettings, container: "BotContainer"):
        self.settings = settings
        self.container = container

    async def handle_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Processes incoming contact form notification."""
        from ..resources.dto import ContactNotificationPayload

        log.debug(f"Bot: ContactProcessor | Action: HandleNotification | request_id={raw_payload.get('request_id')}")

        try:
            payload = ContactNotificationPayload(**raw_payload)
        except Exception as e:
            log.error(f"Bot: ContactProcessor | Action: ValidationFailed | error={e} | payload={raw_payload}")
            return self.handle_failure(raw_payload, str(e))

        request_id = payload.request_id

        # Use the configured contact topic if available
        message_thread_id = self.settings.telegram_topics.get("contact") if self.settings.telegram_topics else None

        # Fetch bot user name dynamically
        bot_username = await self.container.site_settings.aget_field("telegram_bot_username")
        if not bot_username or not str(bot_username).strip():
            log.warning("Bot: ContactProcessor | Action: GetBotUsername | status=NotFound | using_fallback")
            bot_username = ""  # fallback

        # Short preview for the channel
        text = format_contact_preview()

        # Buttons: "Open Bot" and "Delete"
        kb = build_contact_preview_kb(request_id=request_id, bot_username=bot_username, topic_id=message_thread_id)

        log.info(f"Bot: ContactProcessor | Action: Success | request_id={request_id}")
        return UnifiedViewDTO(
            content=ViewResultDTO(text=text, kb=kb),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"contact_{request_id}",
            mode="topic" if message_thread_id else "channel",
            message_thread_id=message_thread_id,
        )

    def handle_failure(self, raw_payload: dict[str, Any], error_msg: str) -> UnifiedViewDTO:
        request_id = raw_payload.get("request_id", "???")
        log.error(f"Bot: ContactProcessor | Action: FailureHandled | request_id={request_id} | error={error_msg}")
        text = f"⚠️ <b>Error processing contact request #{request_id}</b>\n<b>Error:</b> {error_msg}"
        return UnifiedViewDTO(
            content=ViewResultDTO(text=text),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"fail_contact_{request_id}",
            mode="channel",
            message_thread_id=None,
        )
