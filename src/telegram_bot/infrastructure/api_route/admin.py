from loguru import logger as log

from src.telegram_bot.core.api_client import BaseApiClient


class AdminApiProvider:
    """
    API Provider для админ-панели. Обращается к Django для обновления кэша.
    """

    def __init__(self, api_client: BaseApiClient):
        self.api_client = api_client

    async def refresh_contacts_cache(self) -> dict:
        """
        Запрашивает у Django принудительное обновление кэша для Контактов.
        Django сама пересчитает Summary, соберет Details и положит в Redis.
        """
        log.debug("AdminApiProvider | Refreshing contacts cache")
        return await self.api_client._request(
            method="POST",
            endpoint="/api/v1/admin/cache/refresh/",
            json={"domain": "contacts"},
        )

    async def refresh_appointments_cache(self) -> dict:
        """
        Запрашивает у Django принудительное обновление кэша для Бронирований.
        """
        log.debug("AdminApiProvider | Refreshing appointments cache")
        return await self.api_client._request(
            method="POST",
            endpoint="/api/v1/admin/cache/refresh/",
            json={"domain": "appointments"},
        )

    async def process_contact(self, contact_id: int) -> dict:
        """
        Помечает заявку как обработанную в Django.
        """
        log.info(f"AdminApiProvider | Processing contact_id={contact_id}")
        return await self.api_client._request(
            method="POST",
            endpoint=f"/api/v1/admin/contacts/{contact_id}/process/",
        )
