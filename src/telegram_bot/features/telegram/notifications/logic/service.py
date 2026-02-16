from typing import TYPE_CHECKING

from loguru import logger as log

if TYPE_CHECKING:
    from src.telegram_bot.core.container import BotContainer

    from ..contracts.contract import NotificationsDataProvider


class NotificationsService:
    """
    Сервисный слой для фичи Notifications.
    Инкапсулирует работу с API, Redis Cache и ARQ.
    """

    def __init__(self, container: "BotContainer", data_provider: "NotificationsDataProvider"):
        self.container = container
        self.data_provider = data_provider

    async def confirm_appointment(self, appointment_id: int) -> dict:
        """Подтверждает запись в Django и инициирует отправку Email."""
        response = await self.data_provider.confirm_appointment(appointment_id)

        if response.get("success"):
            await self.process_email_notification(appointment_id, status="confirmed")

        return response

    async def cancel_appointment(self, appointment_id: int, reason_code: str, reason_text: str) -> dict:
        """Отменяет запись в Django и инициирует отправку Email."""
        response = await self.data_provider.cancel_appointment(
            appointment_id=appointment_id, reason=reason_code, note=reason_text
        )

        if response.get("success"):
            await self.process_email_notification(appointment_id, status="cancelled", reason_text=reason_text)

        return response

    async def process_email_notification(self, appointment_id: int, status: str, reason_text: str | None = None):
        """Логика постановки задачи на Email в ARQ с использованием кэша Redis."""
        if not self.container.arq_pool:
            log.error("ARQ pool not initialized.")
            return

        cache_manager = self.container.redis.appointment_cache
        appointment_data = await cache_manager.get(appointment_id)

        if not appointment_data:
            log.warning(f"No cached data for appointment {appointment_id}. Email skipped.")
            return

        recipient_email = appointment_data.get("client_email")
        if not recipient_email or recipient_email == "не указан":
            log.error(f"Invalid email for appointment {appointment_id}.")
            return

        # Формируем данные через UI слой (который в свою очередь использует форматтер)
        # Мы можем вызвать UI метод прямо здесь или передать данные в оркестратор
        # Но для чистоты - сервис просто готовит данные для задачи
        from ..ui.ui import NotificationsUI

        ui = NotificationsUI()
        email_data = ui.render_email_data(appointment_data, status, reason_text)

        try:
            await self.container.arq_pool.enqueue_job(
                "send_email_task",
                recipient_email=recipient_email,
                subject=email_data.get("email_subject"),
                template_name="confirmation.html" if status == "confirmed" else "cancellation.html",
                data=email_data,
            )
            log.info(f"Email task enqueued for {recipient_email}")
            await cache_manager.delete(appointment_id)
        except Exception as e:
            log.error(f"Failed to enqueue email task: {e}")
