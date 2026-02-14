from typing import Any

from src.shared.schemas.response import CoreResponseDTO, ResponseHeader
from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.features.telegram.bot_menu.contracts.menu_contract import MenuDiscoveryProvider
from src.telegram_bot.features.telegram.bot_menu.ui.menu_ui import BotMenuUI
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO


class BotMenuOrchestrator(BaseBotOrchestrator):
    """
    Оркестратор главного меню (Дашборда).
    """

    def __init__(self, discovery_provider: MenuDiscoveryProvider, settings: BotSettings):
        super().__init__(expected_state=None)
        self.discovery = discovery_provider
        self.settings = settings
        self.ui = BotMenuUI()

    async def handle_entry(self, user_id: int, payload: Any = None) -> UnifiedViewDTO:
        """
        Вход в меню.
        """
        return await self.render_menu(user_id)

    async def render_menu(self, user_id: int) -> UnifiedViewDTO:
        """
        Рендерит главное меню для конкретного пользователя.
        """
        # 1. Получаем конфиги всех фич
        all_features = self.discovery.get_menu_buttons()

        # 2. Фильтруем по правам доступа
        available_features = {}
        for key, config in all_features.items():
            if self._check_access(user_id, config):
                available_features[key] = config

        # 3. Рендерим UI
        menu_view = self.ui.render_dashboard(available_features)

        return UnifiedViewDTO(menu=menu_view, content=None, chat_id=user_id, session_key=user_id)

    async def handle_menu_click(self, target: str, user_id: int) -> UnifiedViewDTO | None:
        """
        Обрабатывает клик по кнопке меню.
        """
        features_config = self.discovery.get_menu_buttons()
        target_config = features_config.get(target)

        if not target_config:
            return None

        if not self._check_access(user_id, target_config):
            return None

        # Формируем ответ
        response: CoreResponseDTO[None] = CoreResponseDTO(
            header=ResponseHeader(
                success=True, next_state=target_config.get("target_state", target), current_state="menu"
            ),
            payload=None,
        )

        return await self.process_response(response)

    def _check_access(self, user_id: int, config: dict[str, Any]) -> bool:
        """
        Проверяет, есть ли у пользователя доступ к фиче.
        """
        if config.get("is_superuser"):
            return user_id in self.settings.superuser_ids_list

        if config.get("is_admin"):
            is_owner = user_id in self.settings.owner_ids_list
            is_super = user_id in self.settings.superuser_ids_list
            return is_owner or is_super

        return True
