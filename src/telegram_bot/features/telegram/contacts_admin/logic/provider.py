from src.telegram_bot.infrastructure.api_route.admin import AdminApiProvider
from src.telegram_bot.infrastructure.redis.managers.admin.admin_cache import AdminCacheManager

from ..contracts.contract import ContactsAdminDataProvider
from ..resources.dto import ContactDetailDto, ContactPreviewDto, ContactSummaryDto


class ContactsAdminProvider(ContactsAdminDataProvider):
    """
    Провайдер данных, отвечающий за логику «Сначала кэш (Summary/Details), если пусто - дергаем API».
    """

    def __init__(self, cache: AdminCacheManager, api: AdminApiProvider):
        self.cache = cache
        self.api = api

    async def get_summary(self) -> list[ContactSummaryDto]:
        data = await self.cache.get_summary("contacts")
        if not data:
            await self.api.refresh_contacts_cache()
            data = await self.cache.get_summary("contacts")

        if not data:
            return []

        return [ContactSummaryDto(**item) for item in (data.get("categories", []) if isinstance(data, dict) else data)]

    async def get_preview_list(self, category_id: str, is_archive: bool = False) -> list[ContactPreviewDto]:
        data = await self.cache.get_details("contacts")
        if not data:
            await self.api.refresh_contacts_cache()
            data = await self.cache.get_details("contacts")

        if not data:
            return []

        # Фильтруем дамп: нужная категория и статус (обработано или нет)
        filtered = [
            item for item in data if item.get("topic") == category_id and item.get("is_processed") == is_archive
        ]

        # Берем 10 последних
        filtered = filtered[:10]
        return [ContactPreviewDto(**item) for item in filtered]

    async def get_item_detail(self, item_id: int) -> ContactDetailDto | None:
        data = await self.cache.get_details("contacts")
        if not data:
            await self.api.refresh_contacts_cache()
            data = await self.cache.get_details("contacts")

        if not data:
            return None

        # Ищем конкретную заявку в дампе
        item = next((i for i in data if i.get("id") == item_id), None)
        if not item:
            return None

        return ContactDetailDto(**item)

    async def process_item(self, item_id: int) -> bool:
        response = await self.api.process_contact(item_id)
        return response.get("success", False)
