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
        Логика постановки задачи-диспетчера в ARQ.
        Собирает данные для Email и SMS/WhatsApp и отправляет их в воркер.
        """
        if not self.container.arq_pool:
            log.error("ARQ pool not initialized.")
            return

        cache_manager = self.container.redis.appointment_cache
        appointment_data = await cache_manager.get(appointment_id)

        if not appointment_data:
            log.warning(f"No cached data for appointment {appointment_id}. Notification skipped.")
            return

        # --- 1. Подготовка данных для Email ---
        recipient_email = appointment_data.get("client_email")
        # Генерируем данные для email всегда, даже если email не указан (на всякий случай)

        from ..ui.ui import NotificationsUI

        ui = NotificationsUI()
        email_data = ui.render_email_data(appointment_data, status, reason_text)

        email_subject = email_data.get("email_subject")
        email_template = "confirmation.html" if status == "confirmed" else "cancellation.html"

        # --- 2. Подготовка данных для SMS/WhatsApp ---
        sms_text = None
        client_phone = appointment_data.get("client_phone")

        if status == "confirmed" and client_phone:
            from ..resources.texts import NotificationsTexts

            # Парсим дату и время из строки datetime (ожидается "YYYY-MM-DD HH:MM" или похожее)
            # В DTO приходит строкой, попробуем разделить.
            dt_str = str(appointment_data.get("datetime", ""))
            parts = dt_str.split(" ")
            date_part = parts[0] if len(parts) > 0 else dt_str
            time_part = parts[1] if len(parts) > 1 else ""

            sms_text = NotificationsTexts.get_sms_confirm_text(
                first_name=appointment_data.get("first_name", "Cliente"),
                date=date_part,
                time=time_part,
                master=appointment_data.get("master_name", ""),
            )

        # --- 3. Отправка задачи-диспетчера ---
        notification_payload = {
            "appointment_id": appointment_id,
            "email": recipient_email,
            "phone": client_phone,
            "email_subject": email_subject,
            "email_template": email_template,
            "email_data": email_data,
            "sms_text": sms_text,
        }

        try:
            await self.container.arq_pool.enqueue_job(
                "send_appointment_notification",
                notification_data=notification_payload,
            )
            log.info(f"Notification dispatcher task enqueued for ID={appointment_id}")

            # Удаляем из кэша только после успешной постановки задачи
            # (Хотя, возможно, стоит оставить для повторных попыток? Пока удаляем как было)
            await cache_manager.delete(appointment_id)

        except Exception as e:
            log.error(f"Failed to enqueue notification dispatcher task: {e}")
