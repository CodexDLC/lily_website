from typing import TYPE_CHECKING  # <-- Добавлено TYPE_CHECKING

from loguru import logger as log

# from src.workers.notification_worker.services.notification_service import NotificationService # <-- Оригинальный импорт

if TYPE_CHECKING:  # <-- Новый блок для импортов только для проверки типов
    from src.workers.notification_worker.services.notification_service import (
        NotificationService,
    )  # <-- Импорт перемещен сюда


async def send_email_task(
    recipient_email: str,
    subject: str,
    template_name: str,
    data: dict,
    notification_service: "NotificationService",  # <-- Используем строку для аннотации
):
    """
    Задача для отправки email.
    """
    log.info(f"Sending email to {recipient_email} with subject '{subject}' using template '{template_name}'")
    try:
        await notification_service.send_notification(
            email=recipient_email, subject=subject, template_name=template_name, data=data
        )
        log.success(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        log.error(f"Failed to send email to {recipient_email}: {e}", exc_info=True)
