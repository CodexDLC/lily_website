"""
Director — координатор переходов между фичами.
Управляет FSM стейтами и делегирует рендеринг оркестраторам.
"""

from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable  # Добавлен Optional

from aiogram.fsm.context import FSMContext
from loguru import logger

KEY_SESSION_DATA = "session_data"

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer


@runtime_checkable
class OrchestratorProtocol(Protocol):
    async def render(self, payload: Any) -> Any: ...
    # Изменена сигнатура handle_entry для Optional[int]
    async def handle_entry(self, user_id: int | None, payload: Any = None) -> Any: ...
    def set_director(self, director: Any): ...


class Director:
    """
    Координатор переходов между фичами.
    """

    # Изменена сигнатура конструктора для Optional[FSMContext] и Optional[int]
    def __init__(self, container: "BotContainer", state: FSMContext | None = None, user_id: int | None = None):
        self.container = container
        self.state = state
        self.user_id = user_id

    async def set_scene(self, feature: str, payload: Any) -> Any:
        """
        Межфичевый переход: смена FSM State + вызов entry logic.

        Args:
            feature: Имя фичи (ключ в container.features)
            payload: Данные для инициализации (если None -> handle_entry без payload)
        """
        # 1. Получаем оркестратор из контейнера
        orchestrator = self.container.features.get(feature)

        if not orchestrator:
            logger.error(f"Director | unknown_feature='{feature}' user_id={self.user_id}")
            # Можно вернуть экран ошибки, если он есть
            return None

        orchestrator = cast("OrchestratorProtocol", orchestrator)
        if hasattr(orchestrator, "set_director"):
            orchestrator.set_director(self)

        # 2. Смена FSM State
        # Мы договорились, что оркестратор сам ставит стейт внутри handle_entry,
        # но для надежности можно попробовать найти стейт в реестре
        # if self.state and states_group: # Добавлена проверка на self.state
        #     await self.state.set_state(states_group.main)

        # 3. Entry logic
        # Всегда вызываем handle_entry для инициализации фичи
        if hasattr(orchestrator, "handle_entry"):
            # user_id уже Optional, поэтому передаем как есть
            return await orchestrator.handle_entry(self.user_id, payload)

        # Fallback для старых оркестраторов (если они еще есть)
        return await orchestrator.render(payload)

    async def render(self, feature: str, service: str, payload: Any) -> Any:
        """
        Внутрифичевый переход (Legacy метод, если нужен).
        Сейчас лучше использовать set_scene или методы самого оркестратора.
        """
        return await self.set_scene(feature, payload)
