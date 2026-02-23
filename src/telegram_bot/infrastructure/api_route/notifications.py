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

    async def get_available_slots(self, appointment_id: int) -> list[dict]:
        """
        Получение доступных слотов начиная с даты записи через Django API.
        """
        log.debug(f"NotificationsApiProvider | Fetching slots for appointment_id={appointment_id}")
        result = await self.api_client._request(
            method="GET",
            endpoint=f"/api/v1/booking/slots/?appointment_id={appointment_id}",
        )
        return result.get("slots", []) if isinstance(result, dict) else []

    async def send_reschedule_offer(self, appointment_id: int, slots: list[str]) -> dict:
        """
        Отмена записи с причиной reschedule и отправка email клиенту через Django API.
        """
        log.debug(f"NotificationsApiProvider | Sending reschedule offer for appointment_id={appointment_id}")
        return await self.api_client._request(
            method="POST",
            endpoint="/api/v1/booking/appointments/propose/",
            json={"appointment_id": appointment_id, "proposed_slots": slots},
        )
