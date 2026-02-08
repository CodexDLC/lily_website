from typing import Any

from src.shared.schemas.response import CoreResponseDTO, ResponseHeader
from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.features.bot_menu.contracts.menu_contract import MenuDiscoveryProvider
from src.telegram_bot.features.bot_menu.ui.menu_ui import BotMenuUI
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO


class BotMenuOrchestrator(BaseBotOrchestrator):
    """
    Оркестратор главного меню (Дашборда).
    Эмулирует работу бэкенда, собирая ответы из конфигурации фич.
    Поддерживает RBAC (фильтрацию кнопок по флагам is_admin/is_superuser).
    """

    def __init__(self, discovery_provider: MenuDiscoveryProvider, settings: BotSettings):
        super().__init__(expected_state=None)
        self.discovery = discovery_provider
        self.settings = settings
        self.ui = BotMenuUI()

    async def handle_entry(self, user_id: int, payload: Any = None) -> UnifiedViewDTO:
        """
        Вход в меню (обычно вызывается по команде /menu).
        """
        return await self.render_menu(user_id)

    async def render_menu(self, user_id: int) -> UnifiedViewDTO:
        """
        Рендерит главное меню для конкретного пользователя.
        Фильтрует кнопки на основе ролей.
        """
        # 1. Получаем конфиги всех фич
        all_features = self.discovery.get_menu_buttons()

        # 2. Фильтруем по правам доступа
        available_features = {}
        descriptions = []

        for key, config in all_features.items():
            if self._check_access(user_id, config):
                available_features[key] = config

                # Собираем описания только для доступных фич
                if desc := config.get("description"):
                    descriptions.append(f"• {config.get('text', key)}: {desc}")

        # 3. Рендерим UI
        menu_view = self.ui.render_dashboard(available_features)

        return UnifiedViewDTO(menu=menu_view, content=None)

    async def handle_menu_click(self, target: str, user_id: int) -> UnifiedViewDTO | None:
        """
        Обрабатывает клик по кнопке меню.
        Проверяет права доступа перед переходом.
        """
        features_config = self.discovery.get_menu_buttons()
        target_config = features_config.get(target)

        if not target_config:
            return None

        # Проверка прав (защита от умников, которые шлют callback руками)
        if not self._check_access(user_id, target_config):
            # Можно вернуть ошибку "Доступ запрещен"
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
        Использует флаги is_admin и is_superuser.
        """
        # 1. Проверка Superuser (Разработчик)
        if config.get("is_superuser"):
            return user_id in self.settings.superuser_ids_list

        # 2. Проверка Admin (Владелец)
        if config.get("is_admin"):
            # Админ - это или владелец, или суперюзер (суперюзер имеет права владельца)
            is_owner = user_id in self.settings.owner_ids_list
            is_super = user_id in self.settings.superuser_ids_list
            return is_owner or is_super

        # Если флагов нет - доступно всем
        return True
