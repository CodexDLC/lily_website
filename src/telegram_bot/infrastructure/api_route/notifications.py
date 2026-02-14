from typing import Any

from loguru import logger as log

# Импортируем BaseApiClient из core
from src.telegram_bot.core.api_client import BaseApiClient
from src.telegram_bot.features.telegram.notifications.contracts.contract import NotificationsDataProvider


class NotificationsApiProvider(NotificationsDataProvider):
    """
    Реализация NotificationsDataProvider, использующая внешний API.
    """

    def __init__(
        self, api_client: BaseApiClient, resource_path: str = "/notifications"
    ):  # <-- Используем BaseApiClient
        self.api_client = api_client
        self.resource_path = resource_path

    async def get_data(self, user_id: int) -> Any:
        """
        Получение данных через API (CRUD - Read).
        """
        log.debug(f"NotificationsApiProvider | Fetching data for user_id={user_id} via API")
        # Используем _request из BaseApiClient
        return await self.api_client._request(method="GET", endpoint=f"{self.resource_path}/{user_id}")

    async def create_notification(self, user_id: int, data: dict) -> Any:
        """
        Создание уведомления через API (CRUD - Create).
        """
        log.debug(f"NotificationsApiProvider | Creating notification for user_id={user_id} via API")
        return await self.api_client._request(method="POST", endpoint=f"{self.resource_path}/{user_id}", json=data)

    async def update_notification(self, notification_id: int, data: dict) -> Any:
        """
        Обновление уведомления через API (CRUD - Update).
        """
        log.debug(f"NotificationsApiProvider | Updating notification_id={notification_id} via API")
        return await self.api_client._request(
            method="PUT",  # Или PATCH, в зависимости от API
            endpoint=f"{self.resource_path}/{notification_id}",
            json=data,
        )

    async def delete_notification(self, notification_id: int) -> None:
        """
        Удаление уведомления через API (CRUD - Delete).
        """
        log.debug(f"NotificationsApiProvider | Deleting notification_id={notification_id} via API")
        await self.api_client._request(method="DELETE", endpoint=f"{self.resource_path}/{notification_id}")
