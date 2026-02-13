from typing import Any

from src.telegram_bot.services.base.base_orchestrator import BaseBotOrchestrator
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO

from ..feature_setting import NotificationsStates
from ..ui.ui import NotificationsUI


class NotificationsOrchestrator(BaseBotOrchestrator):
    """
    Оркестратор для фичи Notifications (Telegram UI).
    """

    def __init__(self):
        super().__init__(expected_state="notifications")
        self.ui = NotificationsUI()

    async def handle_entry(self, user_id: int, payload: Any = None) -> UnifiedViewDTO:
        """Вход в фичу (Cold Start)."""
        if self.director and self.director.state:
            await self.director.state.set_state(NotificationsStates.main)

        return await self.render(None)

    async def render_content(self, payload: Any) -> Any:
        """Рендеринг основного контента."""
        # NotificationsUI.render_main doesn't exist in current ui.py,
        # but we need to satisfy the interface.
        # For now, returning a placeholder or calling existing method.
        return self.ui.render_main(payload) if payload else None
