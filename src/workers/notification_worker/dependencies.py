from typing import Any, cast

from codex_platform.workers.arq import BaseArqService
from loguru import logger as log

from src.workers.core.base_module.dependencies import (
    DependencyFunction,
    close_common_dependencies,
    init_common_dependencies,
)
from src.workers.core.base_module.orchestrator import NotificationOrchestrator
from src.workers.core.base_module.seven_io_client import SevenIOClient
from src.workers.core.base_module.twilio_service import TwilioService
from src.workers.notification_worker.config import WorkerSettings
from src.workers.notification_worker.services.notification_service import NotificationService


async def init_arq_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация ArqService."""
    log.info("Initializing ArqService...")
    try:
        arq_service = BaseArqService(settings.arq_redis_settings)
        await arq_service.init()
        ctx["arq_service"] = arq_service
        log.info("ArqService initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize ArqService: {e}")
        raise


async def close_arq_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Закрытие ArqService."""
    arq_service = ctx.get("arq_service")
    if arq_service:
        await arq_service.close()
        log.info("ArqService closed.")


async def init_notification_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация NotificationService."""
    log.info("Initializing NotificationService...")
    try:
        site_settings = ctx["site_settings"]

        notification_service = NotificationService(
            templates_dir=str(settings.TEMPLATES_DIR),
            site_url=site_settings.site_base_url,
            logo_url=site_settings.logo_url,
            smtp_host=site_settings.smtp_host,
            smtp_port=site_settings.smtp_port,
            smtp_user=site_settings.smtp_user,
            smtp_password=site_settings.smtp_password,
            smtp_from_email=site_settings.smtp_from_email,
            smtp_use_tls=site_settings.smtp_use_tls,
            sendgrid_api_key=site_settings.sendgrid_api_key,
            url_path_confirm=site_settings.url_path_confirm,
            url_path_cancel=site_settings.url_path_cancel,
            url_path_reschedule=site_settings.url_path_reschedule,
            url_path_contact_form=site_settings.url_path_contact_form,
        )
        ctx["notification_service"] = notification_service
        log.info("NotificationService initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize NotificationService: {e}")
        raise


async def init_seven_io_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация SevenIOClient."""
    log.info("Initializing SevenIOClient...")
    try:
        api_key = settings.SEVEN_IO_API_KEY
        if not api_key:
            log.warning("Seven.io API Key is missing.")
            ctx["seven_io_client"] = None
            return

        seven_io_client = SevenIOClient(api_key=api_key)
        ctx["seven_io_client"] = seven_io_client
        log.info("SevenIOClient initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize SevenIOClient: {e}")
        raise


async def init_twilio_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация TwilioService."""
    log.info("Initializing TwilioService...")
    try:
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            log.warning("Twilio settings are missing.")
            ctx["twilio_service"] = None
            return

        twilio_service = TwilioService(
            account_sid=cast("str", settings.TWILIO_ACCOUNT_SID),
            auth_token=cast("str", settings.TWILIO_AUTH_TOKEN),
            from_number=cast("str", settings.TWILIO_PHONE_NUMBER),
            sendgrid_api_key=settings.SENDGRID_API_KEY,
        )
        ctx["twilio_service"] = twilio_service
        log.info("TwilioService initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize TwilioService: {e}")
        raise


async def init_orchestrator(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация NotificationOrchestrator."""
    log.info("Initializing NotificationOrchestrator...")
    try:
        notification_service = cast("NotificationService", ctx["notification_service"])
        seven_io_client = cast("SevenIOClient", ctx["seven_io_client"])
        twilio_service = cast("TwilioService", ctx["twilio_service"])

        orchestrator = NotificationOrchestrator(
            email_client=notification_service.email_client,
            seven_io_client=seven_io_client,
            twilio_client=twilio_service,
        )
        ctx["orchestrator"] = orchestrator
        log.info("NotificationOrchestrator initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize NotificationOrchestrator: {e}")
        raise


STARTUP_DEPENDENCIES: list[DependencyFunction] = [
    init_common_dependencies,
    init_arq_service,
    init_notification_service,
    init_seven_io_service,
    init_twilio_service,
    init_orchestrator,
]

SHUTDOWN_DEPENDENCIES: list[DependencyFunction] = [
    close_arq_service,
    close_common_dependencies,
]
