from typing import TYPE_CHECKING

from loguru import logger as log

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer

    from ..contracts.contract import NotificationsDataProvider


class NotificationsService:
    """
    Сервисный слой для фичи Notifications.
    Теперь передает в воркер только ID и статус.
    """

    def __init__(self, container: "BotContainer", data_provider: "NotificationsDataProvider"):
        self.container = container
        self.data_provider = data_provider

    async def confirm_appointment(self, appointment_id: int) -> dict:
        """Подтверждает запись в Django и инициирует отправку Email."""
        response = await self.data_provider.confirm_appointment(appointment_id)

        if response.get("success"):
            await self.process_notification(appointment_id, status="confirmed")

        return response

    async def cancel_appointment(self, appointment_id: int, reason_code: str, reason_text: str) -> dict:
        """Отменяет запись в Django и инициирует отправку Email."""
        response = await self.data_provider.cancel_appointment(
            appointment_id=appointment_id, reason=reason_code, note=reason_text
        )

        if response.get("success"):
            await self.process_notification(appointment_id, status="cancelled", reason_text=reason_text)

        return response

    async def process_notification(self, appointment_id: int, status: str, reason_text: str | None = None):
        """
        Ставит задачу в ARQ. Передает минимум данных.
        """
        if not self.container.arq_pool:
            log.error("ARQ pool not initialized.")
            return

        try:
            # Передаем только ID и статус. Воркер сам возьмет данные из Redis.
            await self.container.arq_pool.enqueue_job(
                "send_appointment_notification", appointment_id=appointment_id, status=status, reason_text=reason_text
            )
            log.info(f"Notification task enqueued for ID={appointment_id}")

        except Exception as e:
            log.error(f"Failed to enqueue notification task: {e}")
