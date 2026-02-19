from typing import Any, cast

from loguru import logger as log

from src.shared.core.manager_redis.manager import StreamManager
from src.shared.schemas.site_settings import SiteSettingsSchema
from src.workers.core.base import ArqService
from src.workers.core.base_module.dependencies import (
    DependencyFunction,
    close_common_dependencies,
    init_common_dependencies,
)
from src.workers.core.base_module.twilio_service import TwilioService
from src.workers.notification_worker.config import WorkerSettings
from src.workers.notification_worker.services.notification_service import NotificationService


async def init_arq_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация ArqService."""
    log.info("Initializing ArqService...")
    try:
        arq_service = ArqService(settings.arq_redis_settings)
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


async def init_stream_manager(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация StreamManager."""
    log.info("Initializing Stream Manager...")
    try:
        redis_service = ctx.get("redis_service")
        if not redis_service:
            raise RuntimeError("RedisService not found in context.")
        stream_manager = StreamManager(redis_service)
        ctx["stream_manager"] = stream_manager
        log.info("Stream Manager initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize Stream Manager: {e}")
        raise


async def init_notification_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация NotificationService."""
    log.info("Initializing NotificationService...")
    try:
        site_settings = cast("SiteSettingsSchema | None", ctx.get("site_settings"))
        if not site_settings:
            site_settings = SiteSettingsSchema()

        notification_service = NotificationService(
            templates_dir=str(settings.TEMPLATES_DIR),
            site_url=site_settings.site_base_url,
            logo_url=site_settings.logo_url,
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_user=settings.SMTP_USER,
            smtp_password=settings.SMTP_PASSWORD,
            smtp_from_email=settings.SMTP_FROM_EMAIL,
            smtp_use_tls=settings.SMTP_USE_TLS,
            sendgrid_api_key=settings.SENDGRID_API_KEY,
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


async def init_twilio_service(ctx: dict[str, Any], settings: WorkerSettings) -> None:
    """Инициализация TwilioService."""
    log.info("Initializing TwilioService...")
    try:
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
            log.warning("Twilio settings are missing.")
            ctx["twilio_service"] = None
            return

        # Type narrowing for Mypy
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        phone_number = settings.TWILIO_PHONE_NUMBER

        assert account_sid is not None
        assert auth_token is not None
        assert phone_number is not None

        twilio_service = TwilioService(
            account_sid=account_sid,
            auth_token=auth_token,
            from_number=phone_number,
        )
        ctx["twilio_service"] = twilio_service
        log.info("TwilioService initialized successfully.")
    except Exception as e:
        log.exception(f"Failed to initialize TwilioService: {e}")
        raise


STARTUP_DEPENDENCIES: list[DependencyFunction] = [
    init_common_dependencies,
    init_arq_service,
    init_stream_manager,
    init_notification_service,
    init_twilio_service,
]

SHUTDOWN_DEPENDENCIES: list[DependencyFunction] = [
    close_arq_service,
    close_common_dependencies,
]
