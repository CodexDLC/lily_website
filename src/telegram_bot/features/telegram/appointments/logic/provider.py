from src.telegram_bot.infrastructure.api_route.appointments import AppointmentsApiProvider

from ..resources.dto import AppointmentItemDto, CategorySummaryDto


class AppointmentsProvider:
    """
    Провайдер данных для фичи Appointments.
    Обращается к Django API и преобразует ответы в DTO.
    """

    def __init__(self, api: AppointmentsApiProvider):
        self.api = api

    async def get_summary(self) -> list[CategorySummaryDto]:
        data = await self.api.get_summary()
        if not isinstance(data, dict):
            return []
        return [CategorySummaryDto(**item) for item in data.get("categories", [])]

    async def get_list(self, category_slug: str, page: int = 1) -> tuple[list[AppointmentItemDto], int, int]:
        data = await self.api.get_list(category_slug=category_slug, page=page)
        if not isinstance(data, dict):
            return [], 1, 0
        items = [AppointmentItemDto(**i) for i in data.get("items", [])]
        pages = data.get("pages", 1)
        total = data.get("total", 0)
        return items, pages, total
