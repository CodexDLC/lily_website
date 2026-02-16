from loguru import logger as log

# Импортируем BaseApiClient из core
from src.telegram_bot.core.api_client import BaseApiClient
from src.telegram_bot.features.telegram.notifications.contracts.contract import NotificationsDataProvider


class NotificationsApiProvider(NotificationsDataProvider):
    """
    API Provider для управления заявками (appointments) через Django API.
    Инкапсулирует endpoints и детали взаимодействия с backend.
    """

    def __init__(self, api_client: BaseApiClient):
        self.api_client = api_client

    async def confirm_appointment(self, appointment_id: int) -> dict:
        """
        Подтверждение заявки через Django API.
        """
        log.debug(f"NotificationsApiProvider | Confirming appointment_id={appointment_id}")
        return await self.api_client._request(
            method="POST",
            endpoint="/api/v1/booking/appointments/manage/",
            json={"appointment_id": appointment_id, "action": "confirm"},
        )

    async def cancel_appointment(self, appointment_id: int, reason: str | None = None, note: str | None = None) -> dict:
        """
        Отклонение заявки через Django API.
        """
        log.debug(f"NotificationsApiProvider | Cancelling appointment_id={appointment_id} reason={reason}")
        return await self.api_client._request(
            method="POST",
            endpoint="/api/v1/booking/appointments/manage/",
            json={"appointment_id": appointment_id, "action": "cancel", "cancel_reason": reason, "cancel_note": note},
        )
