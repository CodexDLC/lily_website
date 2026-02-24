from typing import Protocol

from ..resources.dto import AppointmentItemDto, CategorySummaryDto


class AppointmentsDataProvider(Protocol):
    """
    Контракт для доступа к данным фичи Appointments.
    """

    async def get_summary(self) -> list[CategorySummaryDto]:
        """Получить сводку по категориям (всего/ожидает/завершено)."""
        ...

    async def get_list(self, category_slug: str, page: int = 1) -> tuple[list[AppointmentItemDto], int, int]:
        """
        Получить список записей по категории.
        Возвращает (items, total_pages, total_count).
        """
        ...
