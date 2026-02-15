from src.workers.core.tasks import CORE_FUNCTIONS

from .email_tasks import send_email_task
from .notification_tasks import send_booking_notification_task

# Здесь агрегируются задачи для воркера уведомлений
# Мы объединяем специфичные задачи воркера с базовыми задачами из core (ретраи и т.д.)

FUNCTIONS = [
    send_booking_notification_task,
    send_email_task,
] + CORE_FUNCTIONS
