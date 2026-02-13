from .notification_tasks import send_booking_notification_task

# Здесь будут агрегироваться задачи для воркера уведомлений

FUNCTIONS = [
    send_booking_notification_task,
]
