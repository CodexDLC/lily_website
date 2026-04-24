from typing import Any, Protocol


class AppointmentsDataProvider(Protocol):
    """
    Контракт для доступа к данным и действиям с записями (Appointments).
    Используется в оркестраторе и процессорах, чтобы не зависеть от конкретной реализации (например, AppointmentsApiProvider).
    """

    async def get_summary(self) -> dict[str, Any]:
        """Получение сводки по записям."""
        ...

    async def get_list(self, category_slug: str, page: int = 1) -> dict[str, Any]:
        """Получение списка записей по категории с пагинацией."""
        ...

    async def expire_reschedule(self, appointment_id: int) -> dict[str, Any]:
        """Отправляет команду на истечение срока переноса записи."""
        ...
