from typing import TYPE_CHECKING, Any

from loguru import logger as log

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.services.base import UnifiedViewDTO, ViewResultDTO

from ..resources.formatters import format_contact_preview
from ..resources.keyboards import build_contact_preview_kb

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


class ContactProcessor:
    """
    Процессор для обработки уведомлений из контактной формы.
    Отправляет превью-сообщение с кнопкой "Открыть бота" в основной чат (General).
    """

    def __init__(self, settings: BotSettings, container: "BotContainer"):
        self.settings = settings
        self.container = container

    async def handle_notification(self, raw_payload: dict[str, Any]) -> UnifiedViewDTO:
        """Обрабатывает входящее уведомление из контактной формы."""
        from ..resources.dto import ContactNotificationPayload

        try:
            payload = ContactNotificationPayload(**raw_payload)
        except Exception as e:
            log.error(f"ContactProcessor | Validation error: {e}")
            return self.handle_failure(raw_payload, str(e))

        request_id = payload.request_id

        # Для контактных форм принудительно используем General (без топика)
        message_thread_id = None

        # Fetch bot user name dynamically
        bot_username = await self.container.site_settings.get_field("telegram_bot_username")
        if not bot_username or not str(bot_username).strip():
            bot_username = ""  # fallback

        # Краткое превью в канал (текст берется из Texts)
        text = format_contact_preview()

        # Кнопки: «Открыть бота» и «Удалить»
        kb = build_contact_preview_kb(request_id=request_id, bot_username=bot_username, topic_id=message_thread_id)

        return UnifiedViewDTO(
            content=ViewResultDTO(text=text, kb=kb),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"contact_{request_id}",
            mode="channel",
            message_thread_id=message_thread_id,
        )

    def handle_failure(self, raw_payload: dict[str, Any], error_msg: str) -> UnifiedViewDTO:
        request_id = raw_payload.get("request_id", "???")
        text = f"⚠️ <b>Ошибка обработки заявки #{request_id}</b>\n<b>Ошибка:</b> {error_msg}"
        return UnifiedViewDTO(
            content=ViewResultDTO(text=text),
            chat_id=self.settings.telegram_admin_channel_id,
            session_key=f"fail_contact_{request_id}",
            mode="channel",
            message_thread_id=None,
        )
