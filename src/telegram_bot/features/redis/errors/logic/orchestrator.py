from typing import Any

from codex_bot.base import BaseBotOrchestrator, UnifiedViewDTO
from codex_bot.director import Director

from src.telegram_bot.features.redis.errors.ui.error_ui import ErrorUI


class ErrorOrchestrator(BaseBotOrchestrator[Any]):
    """
    Оркестратор для отображения системных ошибок.
    """

    def __init__(self):
        super().__init__(expected_state=None)
        self.ui = ErrorUI()

    def handle_error(self, message_data: dict[str, Any]) -> UnifiedViewDTO:
        error_text = str(message_data.get("error") or message_data.get("message") or message_data)
        return UnifiedViewDTO(content=self.ui.render_error({"error": error_text}))

    async def handle_entry(self, director: Director, payload: Any = None) -> UnifiedViewDTO:
        """
        Точка входа.
        """
        # Если payload содержит текст ошибки, используем его
        error_text = str(payload) if payload else "Unknown system error occurred."
        return await self.render(director=director, payload=error_text)

    async def render_content(self, director: Director | None = None, payload: Any = None) -> Any:
        """
        Рендерит сообщение об ошибке.
        Ожидает словарь для ErrorUI.
        """
        return self.ui.render_error({"error": str(payload)})
