from typing import Any

from src.telegram_bot.features.redis.errors.resources.errors_map import DEFAULT_ERRORS
from src.telegram_bot.features.redis.errors.ui.ui import ErrorUI
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO


class ErrorOrchestrator(BaseBotOrchestrator):
    """
    Оркестратор для отображения ошибок.
    Принимает код ошибки (payload), находит конфиг и рисует экран.
    """

    def __init__(self):
        super().__init__(expected_state="error")
        self.ui = ErrorUI()

        # Объединяем дефолтные ошибки с пользовательскими (если есть)
        self.errors_map = DEFAULT_ERRORS.copy()
        # if hasattr(settings, "CUSTOM_ERRORS"):
        #     self.errors_map.update(settings.CUSTOM_ERRORS)

    async def handle_entry(self, user_id: int, payload: Any = None) -> UnifiedViewDTO:
        """
        Вход в экран ошибки.
        payload: код ошибки (str) или объект исключения.
        """
        error_code = "default"

        if isinstance(payload, str):
            error_code = payload
        elif hasattr(payload, "code"):  # Если это кастомное исключение с кодом
            error_code = payload.code

        # Если код не найден, используем default
        if error_code not in self.errors_map:
            error_code = "default"

        return await self.render(error_code)

    async def render_content(self, payload: Any) -> Any:
        """
        Отрисовка ошибки по коду.
        """
        error_code = payload
        error_config = self.errors_map.get(error_code, self.errors_map["default"])

        return self.ui.render_error(error_config)
