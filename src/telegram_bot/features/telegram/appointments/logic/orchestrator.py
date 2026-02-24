from typing import Any

from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO, ViewResultDTO

from ..resources.callbacks import AppointmentsCallback
from ..ui.ui import AppointmentsUI
from .provider import AppointmentsProvider


class AppointmentsOrchestrator(BaseBotOrchestrator):
    def __init__(self, provider: AppointmentsProvider, url_signer, site_settings):
        super().__init__(expected_state="appointments")
        self.provider = provider
        self.url_signer = url_signer
        self.site_settings = site_settings
        self.ui = AppointmentsUI()

    async def handle_entry(self, user_id: int, chat_id: int | None = None, payload: Any = None) -> UnifiedViewDTO:
        """Вход в фичу (Cold Start). Показываем Hub."""
        return await self.render(payload=None)

    async def render_content(self, payload: Any) -> ViewResultDTO:
        """
        Отрисовка контента в зависимости от payload:
        - None          → Hub (Экран 0)
        - "dashboard"   → Dashboard по категориям (Экран 1)
        - dict с "category" → Список записей по категории (Экран 2)
        """

        # Hub
        if payload is None:
            return self.ui.render_hub()

        # Dashboard
        if payload == "dashboard":
            summaries = await self.provider.get_summary()
            return self.ui.render_dashboard(summaries)

        # Category list
        if isinstance(payload, dict) and "category" in payload:
            slug = payload["category"]
            page = payload.get("page", 1)

            items, pages, total = await self.provider.get_list(slug, page)

            # Находим название категории из сводки
            summaries = await self.provider.get_summary()
            category_title = next(
                (s.category_title for s in summaries if s.category_slug == slug),
                slug.capitalize(),
            )

            user_id = self.director.user_id if self._director else 0
            base_url = await self.site_settings.get_field("site_base_url") or "https://lily-salon.de"

            tma_url = (
                self.url_signer.generate_signed_url(base_url, user_id, action="appointments") + f"&category={slug}"
            )
            tma_url_new = (
                self.url_signer.generate_signed_url(base_url, user_id, action="appointments_new") + f"&category={slug}"
            )

            return self.ui.render_category(
                category_title=category_title,
                items=items,
                page=page,
                pages=pages,
                total=total,
                slug=slug,
                tma_url=tma_url,
                tma_url_new=tma_url_new,
            )

        return self.ui.render_hub()

    async def handle_action(self, callback_data: AppointmentsCallback) -> UnifiedViewDTO:
        """Обработка нажатий на инлайн-кнопки."""
        action = callback_data.action

        if action == "hub":
            return await self.render(payload=None)

        elif action == "dashboard":
            return await self.render(payload="dashboard")

        elif action == "category" or action in ("prev", "next"):
            return await self.render(payload={"category": callback_data.target, "page": callback_data.page})

        elif action == "soon":
            # Заглушка — остаёмся на Hub
            return await self.render(payload=None)

        elif action == "noop":
            # Кнопка текущей страницы — ничего не делаем, возвращаем текущий экран
            if callback_data.target:
                return await self.render(payload={"category": callback_data.target, "page": callback_data.page})
            return await self.render(payload="dashboard")

        return await self.render(payload=None)
