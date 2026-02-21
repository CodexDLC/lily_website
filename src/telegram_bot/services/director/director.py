"""
Director — координатор переходов между фичами.
Управляет FSM стейтами и делегирует рендеринг оркестраторам.
"""

from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

from aiogram.fsm.context import FSMContext
from loguru import logger

from src.telegram_bot.services.base.view_dto import UnifiedViewDTO

KEY_SESSION_DATA = "session_data"

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


@runtime_checkable
class OrchestratorProtocol(Protocol):
    async def render(self, payload: Any) -> Any: ...
    async def handle_entry(self, user_id: int | None, chat_id: int | None = None, payload: Any = None) -> Any: ...
    def set_director(self, director: Any): ...


class Director:
    """
    Координатор переходов между фичами.
    """

    def __init__(
        self,
        container: "BotContainer",
        state: FSMContext | None = None,
        user_id: int | None = None,
        chat_id: int | None = None,
        trigger_id: int | None = None,
    ):
        self.container = container
        self.state = state
        self.user_id = user_id
        self.chat_id = chat_id
        self.trigger_id = trigger_id

    async def set_scene(self, feature: str, payload: Any) -> Any:
        """
        Межфичевый переход: смена FSM State и вызов логики.
        """
        orchestrator = self.container.features.get(feature)

        if not orchestrator:
            logger.error(f"Director | unknown_feature='{feature}' user_id={self.user_id}")
            return None

        # 1. Смена стейта (если оркестратор его определяет)
        if hasattr(orchestrator, "expected_state") and orchestrator.expected_state and self.state:
            await self.state.set_state(orchestrator.expected_state)

        orchestrator = cast("OrchestratorProtocol", orchestrator)
        if hasattr(orchestrator, "set_director"):
            orchestrator.set_director(self)

        # 2. Вызываем handle_entry или render
        if hasattr(orchestrator, "handle_entry"):
            view = await orchestrator.handle_entry(user_id=self.user_id, chat_id=self.chat_id, payload=payload)
        else:
            view = await orchestrator.render(payload)

        # 3. Пробрасываем данные для сендера (чтобы он нашел месседж-айди в редисе)
        if isinstance(view, UnifiedViewDTO):
            view.chat_id = view.chat_id or self.chat_id
            view.session_key = view.session_key or self.user_id

        return view

    async def render(self, feature: str, service: str, payload: Any) -> Any:
        return await self.set_scene(feature, payload)
