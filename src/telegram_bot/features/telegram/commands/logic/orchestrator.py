"""
Оркестратор фичи commands.
"""

from typing import Any

from aiogram.types import User
from codex_bot.base import BaseBotOrchestrator, UnifiedViewDTO
from codex_bot.director import Director

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.features.telegram.commands.contracts.commands_contract import AuthDataProvider
from src.telegram_bot.features.telegram.commands.resources.dto import UserUpsertDTO
from src.telegram_bot.features.telegram.commands.ui.commands_ui import CommandsUI


class StartOrchestrator(BaseBotOrchestrator[Any]):
    """
    Оркестратор стартового экрана (Welcome Screen).
    """

    def __init__(self, auth_provider: AuthDataProvider, ui: CommandsUI, settings: BotSettings):
        super().__init__(expected_state=None)
        self.auth = auth_provider
        self.ui = ui
        self.settings = settings

    async def render_content(
        self,
        director: Director | None = None,
        payload: Any = None,
    ):
        """
        Стандартный метод рендеринга.
        """
        user_name = payload if isinstance(payload, str) else "User"
        user_id = int(director.session_key) if director and director.session_key is not None else 0
        is_admin = user_id in self.settings.owner_ids_list or user_id in self.settings.superuser_ids_list

        return self.ui.render_welcome_screen(user_name, is_admin=is_admin)

    async def render_welcome(self, user_id: int, chat_id: int | str | None, user_name: str = "User") -> UnifiedViewDTO:
        """Внутренний метод для отрисовки приветствия."""
        is_admin = user_id in self.settings.owner_ids_list or user_id in self.settings.superuser_ids_list

        menu_view = self.ui.render_welcome_screen(user_name, is_admin=is_admin)

        return UnifiedViewDTO(
            menu=menu_view,
            content=None,
            clean_history=True,
            chat_id=chat_id or user_id,
            session_key=user_id,
        )

    async def handle_entry(self, director: Director, payload: Any = None) -> UnifiedViewDTO:
        """
        Точка входа.
        """
        user: User | None = payload if isinstance(payload, User) else None
        user_id = int(director.session_key) if director.session_key is not None else 0

        if user:
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

        return await self.render_welcome(user_id=user_id, chat_id=director.context_id, user_name=user_name)
