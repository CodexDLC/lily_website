from loguru import logger

from src.workers.core.tasks import CORE_FUNCTIONS

from .email_tasks import send_email_task
from .message_tasks import send_appointment_notification, send_message_task
from .notification_tasks import (
    expire_reservation_task,
    send_booking_notification_task,
    send_contact_notification_task,
)

# Aggregating tasks for the notification worker.
# We combine worker-specific tasks with core tasks (retries, etc.).

FUNCTIONS = [
    send_booking_notification_task,
    send_contact_notification_task,
    expire_reservation_task,
    send_email_task,
    send_appointment_notification,
    send_message_task,
] + CORE_FUNCTIONS

logger.info(f"Worker: Aggregator | Action: Initialized | tasks_count={len(FUNCTIONS)}")
