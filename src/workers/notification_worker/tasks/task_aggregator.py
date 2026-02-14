from .email_tasks import send_email_task  # send_batch_emails_task удален
from .notification_tasks import send_booking_notification_task

# Здесь будут агрегироваться задачи для воркера уведомлений

FUNCTIONS = [
    send_booking_notification_task,
    send_email_task,  # Добавляем задачу для отправки одного письма
]
