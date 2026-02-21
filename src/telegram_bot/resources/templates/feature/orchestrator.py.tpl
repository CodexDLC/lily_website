from typing import Any
from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO
from src.telegram_bot.features.{feature_key}.ui.ui import {class_name}UI
from src.telegram_bot.features.{feature_key}.feature_setting import {class_name}States

class {class_name}Orchestrator(BaseBotOrchestrator):
    def __init__(self):
        super().__init__(expected_state="{feature_key}")
        self.ui = {class_name}UI()

    async def handle_entry(self, user_id: int, chat_id: int | None = None, payload: Any = None) -> UnifiedViewDTO:
        """Вход в фичу (Cold Start). Вызывается Director или handler."""
        return await self.render(payload=payload)

    async def render_content(self, payload: Any) -> Any:
        \"\"\"Отрисовка контента\"\"\"
        return self.ui.render_main(payload)
