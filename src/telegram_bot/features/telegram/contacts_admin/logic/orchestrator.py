from typing import Any

from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO, ViewResultDTO

from ..resources.callbacks import ContactsAdminCallback
from ..ui.ui import ContactsAdminUI
from .provider import ContactsAdminProvider


class ContactsAdminOrchestrator(BaseBotOrchestrator):
    def __init__(self, provider: ContactsAdminProvider, url_signer, site_settings):
        super().__init__(expected_state="contacts_admin")
        self.provider = provider
        self.url_signer = url_signer
        self.site_settings = site_settings
        self.ui = ContactsAdminUI()

    async def handle_entry(self, user_id: int, chat_id: int | None = None, payload: Any = None) -> UnifiedViewDTO:
        """Вход в фичу (Cold Start). Показываем Дашборд."""
        return await self.render(payload=payload)

    async def render_content(self, payload: Any) -> ViewResultDTO:
        """Отрисовка контента в зависимости от переданного payload."""

        # 1. Список превью категории (Level 2)
        if isinstance(payload, str) and payload or (isinstance(payload, dict) and payload.get("category_id")):
            if isinstance(payload, dict):
                category_id = payload["category_id"]
                is_archive = payload.get("is_archive", False)
            else:
                category_id = payload
                is_archive = False

            # Получаем список
            previews = await self.provider.get_preview_list(category_id, is_archive=is_archive)
            summary_list = await self.provider.get_summary()

            summary = next((s for s in summary_list if s.category_id == category_id), None)
            category_name = summary.category_name if summary else category_id
            unread_count = summary.unread_count if summary else 0

            user_id = self.director.user_id if self._director else 0

            # Получаем актуальный базовый URL сайта из настроек
            base_url = await self.site_settings.get_field("site_base_url") or "https://lily-salon.de"

            # Подписываем ссылки для открытия в TMA
            tma_url_new = (
                self.url_signer.generate_signed_url(base_url, user_id, action="contacts") + f"&tab={category_id}"
            )
            tma_url_archive = self.url_signer.generate_signed_url(base_url, user_id, action="contacts") + "&tab=archive"

            # Если это архив, заголовок другой
            display_name = f"{category_name} (Архив)" if is_archive else category_name

            return self.ui.render_preview_list(
                display_name, unread_count, previews, category_id, tma_url_new, tma_url_archive
            )

        # 2. Дашборд (Level 1)
        summaries = await self.provider.get_summary()
        return self.ui.render_dashboard(summaries)

    async def handle_action(self, callback_data: ContactsAdminCallback) -> UnifiedViewDTO:
        """Обработка нажатий на инлайн-кнопки."""

        # Переход в категорию (Новое)
        if callback_data.action == "category":
            return await self.render(payload=callback_data.target)

        # Переход в категорию (Архив)
        elif callback_data.action == "archive":
            return await self.render(payload={"category_id": callback_data.target, "is_archive": True})

        elif callback_data.action == "back":
            return await self.render(payload=None)

        elif callback_data.action == "refresh":
            await self.provider.api.refresh_contacts_cache()
            return await self.render(payload=None)

        return await self.render(payload=None)
