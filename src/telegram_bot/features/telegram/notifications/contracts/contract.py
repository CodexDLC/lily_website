from typing import Protocol


class NotificationsDataProvider(Protocol):
    """
    Контракт для доступа к данным фичи Notifications.
    """

    async def confirm_appointment(self, appointment_id: int) -> dict:
        """Подтвердить заявку."""
        ...

    async def cancel_appointment(self, appointment_id: int, reason: str | None = None, note: str | None = None) -> dict:
        """Отклонить заявку."""
        ...

    async def get_available_slots(self, appointment_id: int) -> list[dict]:
        """Получить доступные слоты начиная с даты записи."""
        ...

    async def send_reschedule_offer(self, appointment_id: int, slots: list[str]) -> dict:
        """Отменить запись с причиной reschedule и отправить клиенту email с предложением."""
        ...
