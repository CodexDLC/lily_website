from typing import TYPE_CHECKING, Any, cast

from src.shared.schemas.response import CoreResponseDTO
from src.telegram_bot.services.base.view_dto import UnifiedViewDTO

if TYPE_CHECKING:
    from src.telegram_bot.services.director.director import Director


class BaseBotOrchestrator:
    """
    Базовый класс оркестратора.
    Определяет контракт жизненного цикла фичи:
    - handle_entry(user_id, payload): Инициализация (загрузка данных) при входе.
    - render(payload): Отрисовка готовых данных.
    """

    def __init__(self, expected_state: str | None):
        self.expected_state = expected_state
        self._director: Director | None = None

    def set_director(self, director: "Director") -> None:
        self._director = director

    @property
    def director(self) -> "Director":
        if not self._director:
            raise RuntimeError(f"Director not set for {self.__class__.__name__}")
        return self._director

    async def handle_entry(self, user_id: int, payload: Any = None) -> UnifiedViewDTO:
        """
        Точка входа в фичу (Cold Start).
        Вызывается Директором, когда payload не передан (или передан для инициализации).
        Задача: загрузить данные и вызвать self.render().
        """
        # Дефолтная реализация: пытаемся отрендерить без данных (для статических экранов)
        return await self.render(payload)

    async def render_content(self, payload: Any) -> Any:
        """
        Превращает бизнес-данные (payload) в ViewDTO контента.
        Должен быть реализован в наследниках.
        """
        raise NotImplementedError(f"render_content not implemented in {self.__class__.__name__}")

    async def render(self, payload: Any) -> UnifiedViewDTO:
        """
        Основной метод рендеринга (Hot Start).
        Вызывается Директором, когда payload уже есть (например, ответ от API).
        """
        if isinstance(payload, CoreResponseDTO):
            return await self.process_response(payload)

        # Если пришел просто payload, рендерим контент
        content_view = await self.render_content(payload)
        return UnifiedViewDTO(content=content_view, menu=None)

    async def process_response(self, response: CoreResponseDTO) -> UnifiedViewDTO:
        """
        Универсальный метод обработки ответа.
        """
        # 1. Проверка навигации
        if response.header.next_state and response.header.next_state != self.expected_state:
            result = await self.director.set_scene(feature=response.header.next_state, payload=response.payload)
            return cast("UnifiedViewDTO", result)

        # 2. Рендер контента
        content_view = None
        if response.payload is not None:
            content_view = await self.render_content(response.payload)

        return UnifiedViewDTO(content=content_view, menu=None)
