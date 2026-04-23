import os
from pathlib import Path

from arq.connections import RedisSettings
from codex_platform.workers.arq import BaseWorkerConfig
from pydantic import Field
from pydantic_settings import SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_FILE_PATH = ROOT_DIR / ".env"


class WorkerSettings(BaseWorkerConfig):
    """Runtime settings shared by all ARQ worker processes."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Redis / project namespace
    project_name: str = Field(default="lily_backend", alias="PROJECT_NAME")
    redis_url_env: str | None = Field(default=None, alias="REDIS_URL")
    redis_site_settings_key: str = "site_settings"
    redis_site_settings_project: str = "lily_backend"

    # Logging fields consumed by codex_core.common.loguru_setup.setup_logging.
    log_level_console: str = "INFO"
    log_level_file: str = "DEBUG"
    log_rotation: str = "10 MB"
    log_dir_name: str = "logs"

    @property
    def is_inside_docker(self) -> bool:
        """Determines if the code is running inside a Docker container."""
        return os.environ.get("IS_DOCKER", "False").lower() in ("true", "1", "t") or os.path.exists("/.dockerenv")

    @property
    def log_dir(self) -> str:
        """Absolute path to the logs folder in the project root."""
        return str(ROOT_DIR / self.log_dir_name)

    @log_dir.setter
    def log_dir(self, value: str) -> None:
        """
        Dummy setter to satisfy LoggingSettingsProtocol.
        Required because setup_logging expects log_dir to be settable.
        """
        pass

    @property
    def service_name_suffix(self) -> str:
        """Suffix for service name when running locally."""
        return "" if self.is_inside_docker else "_local"

    # Redefine log properties to include suffix if needed
    @property
    def log_file_debug(self) -> str:
        service_name = f"{self.project_name}{self.service_name_suffix}"
        return f"{self.log_dir}/{service_name}/debug.log"

    @property
    def log_file_errors(self) -> str:
        service_name = f"{self.project_name}{self.service_name_suffix}"
        return f"{self.log_dir}/{service_name}/errors.json"

    # Notification vendor settings
    SENDGRID_API_KEY: str | None = None
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None
    SEVEN_IO_API_KEY: str | None = None
    TWILIO_WHATSAPP_TEMPLATE_SID: str = "HXd8c4bef13f103fbd4f0796cd2ad03e8e"

    # Worker templates
    TEMPLATES_DIR: str = "src/workers/templates"

    # Internal backend API
    backend_api_base_url: str = Field(default="http://backend:8000/api", alias="BACKEND_API_BASE_URL")
    tracking_worker_api_key: str | None = Field(default=None, alias="TRACKING_WORKER_API_KEY")
    conversations_import_api_key: str | None = Field(default=None, alias="CONVERSATIONS_IMPORT_API_KEY")
    booking_worker_api_key: str | None = Field(default=None, alias="BOOKING_WORKER_API_KEY")
    ops_worker_api_key: str | None = Field(default=None, alias="OPS_WORKER_API_KEY")
    internal_api_timeout: float = 30.0

    # IMAP import v1
    imap_host: str | None = Field(default=None, alias="IMAP_HOST")
    imap_port: int = Field(default=993, alias="IMAP_PORT")
    imap_user: str | None = Field(default=None, alias="IMAP_USER")
    imap_password: str | None = Field(default=None, alias="IMAP_PASSWORD")
    imap_folder: str = Field(default="INBOX", alias="IMAP_FOLDER")
    imap_spam_folder: str = Field(default="Spam", alias="IMAP_SPAM_FOLDER")
    imap_archive_folder: str = Field(default="Archive", alias="IMAP_ARCHIVE_FOLDER")
    email_import_batch_size: int = Field(default=20, alias="EMAIL_IMPORT_BATCH_SIZE")
    email_import_interval_sec: int = Field(default=300, alias="EMAIL_IMPORT_INTERVAL_SEC")
    email_import_stale_after_sec: int = Field(default=900, alias="EMAIL_IMPORT_STALE_AFTER_SEC")
    email_import_max_body_chars: int = Field(default=262_144, alias="EMAIL_IMPORT_MAX_BODY_CHARS")
    email_import_max_raw_bytes: int = Field(default=2_097_152, alias="EMAIL_IMPORT_MAX_RAW_BYTES")

    tracking_flush_interval_sec: int = Field(default=1800, alias="TRACKING_FLUSH_INTERVAL_SEC")
    tracking_flush_stale_after_sec: int = Field(default=3900, alias="TRACKING_FLUSH_STALE_AFTER_SEC")
    booking_worker_interval_sec: int = Field(default=900, alias="BOOKING_WORKER_INTERVAL_SEC")
    booking_worker_stale_after_sec: int = Field(default=2700, alias="BOOKING_WORKER_STALE_AFTER_SEC")

    @property
    def effective_redis_host(self) -> str:
        return "redis" if self.redis_host == "localhost" and Path("/.dockerenv").exists() else self.redis_host

    @property
    def redis_url(self) -> str:
        return self.redis_url_env or super().redis_url.replace(self.redis_host, self.effective_redis_host, 1)

    @property
    def arq_redis_settings(self) -> RedisSettings:
        if self.redis_url_env:
            return RedisSettings.from_dsn(self.redis_url_env)
        return RedisSettings(
            host=self.effective_redis_host,
            port=self.redis_port,
            password=self.redis_password,
        )
