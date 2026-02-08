"""
Оркестратор фичи commands.
Координирует работу между контрактом (данные) и UI (отображение).
"""

from typing import Any

from aiogram.types import User

from src.shared.schemas.user import UserUpsertDTO
from src.telegram_bot.features.commands.contracts.commands_contract import AuthDataProvider
from src.telegram_bot.features.commands.ui.commands_ui import CommandsUI
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO


class StartOrchestrator(BaseBotOrchestrator):
    """
    Оркестратор стартового экрана.
    Singleton: создаётся один раз в container, user передаётся через handle_entry(payload).
    """

    def __init__(self, auth_provider: AuthDataProvider, ui: CommandsUI):
        super().__init__(expected_state=None)
        self.auth = auth_provider
        self.ui = ui

    async def render(self, payload: Any = None) -> UnifiedViewDTO:
        """Превращает имя пользователя в готовый UI."""
        user_name = payload if isinstance(payload, str) else "User"
        menu_view = self.ui.render_start_screen(user_name)
        return UnifiedViewDTO(menu=menu_view, content=None, clean_history=True)

    async def handle_entry(self, user_id: int, payload: Any = None) -> UnifiedViewDTO:
        """
        Точка входа (вызывается из Director или handler).
        payload: User объект aiogram или None.
        """
        user: User | None = payload if isinstance(payload, User) else None

        if user:
            # Sync user через контракт (API или Repository)
            user_dto = UserUpsertDTO(
                telegram_id=user.id,
                first_name=user.first_name,
                username=user.username,
                last_name=user.last_name,
                language_code=user.language_code,
                is_premium=bool(user.is_premium),
            )
            await self.auth.upsert_user(user_dto)
            user_name = user.first_name or "User"
        else:
            user_name = "User"

        return await self.render(user_name)
