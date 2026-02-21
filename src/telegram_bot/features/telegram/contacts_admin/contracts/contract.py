from typing import Protocol

from ..resources.dto import ContactDetailDto, ContactPreviewDto, ContactSummaryDto


class ContactsAdminDataProvider(Protocol):
    async def get_summary(self) -> list[ContactSummaryDto]:
        """
        Получает сводку по категориям (Сначала кэш, потом API).
        """
        ...

    async def get_preview_list(self, category_id: str, is_archive: bool = False) -> list[ContactPreviewDto]:
        """
        Получает список 10 последних заявок в выбранной категории (из кэша).
        Если is_archive=True - берет обработанные, иначе - новые.
        """
        ...

    async def get_item_detail(self, item_id: int) -> ContactDetailDto | None:
        """
        Получает полные данные по одной заявке (из кэша).
        """
        ...

    async def process_item(self, item_id: int) -> bool:
        """
        Помечает заявку как обработанную (через API).
        """
        ...
