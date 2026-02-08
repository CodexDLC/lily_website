"""
UI сервис для фичи commands.
Преобразует данные в готовые ViewResultDTO для отправки пользователю.
"""

from src.telegram_bot.services.base.view_dto import ViewResultDTO
from src.telegram_bot.features.commands.resources.texts import START_GREETING
from src.telegram_bot.features.commands.resources.keyboards import build_start_keyboard


class CommandsUI:
    """
    Pure transformation: Data -> ViewResultDTO.
    Без side effects, без обращений к API.
    """

    def render_start_screen(self, user_name: str) -> ViewResultDTO:
        """Рендерит стартовый экран."""
        text = START_GREETING.format(first_name=user_name)
        kb = build_start_keyboard()
        return ViewResultDTO(text=text, kb=kb)
