from loguru import logger as log

from src.telegram_bot.core.api_client import BaseApiClient


class AppointmentsApiProvider:
    """
    API Provider для получения данных о записях из Django backend.
    Инкапсулирует endpoints и детали взаимодействия с backend.
    """

    def __init__(self, api_client: BaseApiClient):
        self.api_client = api_client

    async def get_summary(self) -> dict:
        """
        Получение сводки по категориям (всего/ожидает/завершено).
        """
        log.debug("AppointmentsApiProvider | Fetching appointments summary")
        return await self.api_client._request("GET", "/api/v1/booking/appointments/summary/")

    async def get_list(self, category_slug: str, page: int = 1) -> dict:
        """
        Получение списка записей по категории с пагинацией.
        """
        log.debug(f"AppointmentsApiProvider | Fetching appointments list: category={category_slug} page={page}")
        return await self.api_client._request(
            "GET",
            f"/api/v1/booking/appointments/list/?category_slug={category_slug}&page={page}",
        )

    async def expire_reschedule(self, appointment_id: int) -> dict:
        """
        Отправляет команду на истечение срока переноса записи.
        """
        log.debug(f"AppointmentsApiProvider | Requesting expire reschedule for ID={appointment_id}")
        return await self.api_client._request(
            "POST",
            "/api/v1/booking/appointments/expire/",
            json={"appointment_id": appointment_id},
        )
