from codex_platform.workers.arq import CORE_FUNCTIONS
from loguru import logger

from .booking import booking_maintenance_task
from .email_import import import_emails_task
from .tracking import flush_tracking_task

FUNCTIONS = [
    import_emails_task,
    flush_tracking_task,
    booking_maintenance_task,
] + CORE_FUNCTIONS

logger.info(f"SystemWorker: Aggregator | Action: Initialized | tasks_count={len(FUNCTIONS)}")
