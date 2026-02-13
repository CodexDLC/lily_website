from typing import Any, Protocol


class NotificationsDataProvider(Protocol):
    """
    Контракт для доступа к данным фичи Notifications.
    Реализация (Client или Repository) подставляется через DI.
    """

    async def get_data(self, user_id: int) -> Any:
        """Пример метода получения данных."""
        ...
