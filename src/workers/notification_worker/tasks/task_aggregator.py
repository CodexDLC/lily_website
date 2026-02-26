from loguru import logger

from src.workers.core.tasks import CORE_FUNCTIONS

from .email_tasks import send_email_task
from .notification_tasks import (
    expire_reservation_task,
    send_booking_notification_task,
    send_contact_notification_task,
)
from .twilio_tasks import send_appointment_notification, send_twilio_task

# Aggregating tasks for the notification worker.
# We combine worker-specific tasks with core tasks (retries, etc.).

FUNCTIONS = [
    send_booking_notification_task,
    send_contact_notification_task,
    expire_reservation_task,
    send_email_task,
    send_appointment_notification,
    send_twilio_task,
] + CORE_FUNCTIONS

logger.info(f"Worker: Aggregator | Action: Initialized | tasks_count={len(FUNCTIONS)}")
