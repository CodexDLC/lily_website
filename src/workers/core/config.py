from pydantic import Field

from src.shared.core.config import CommonSettings


class WorkerSettings(CommonSettings):
    """
    Настройки для Notification Worker (arq).
    """

    # --- Email (SMTP) ---
    SMTP_HOST: str = "smtp.spacemail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_USE_TLS: bool = True

    # --- SendGrid API (Fallback) ---
    SENDGRID_API_KEY: str | None = None

    # --- Twilio ---
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_PHONE_NUMBER: str | None = None

    # WhatsApp Content Template SID
    TWILIO_WHATSAPP_TEMPLATE_SID: str = "HXd8c4bef13f103fbd4f0796cd2ad03e8e"

    # --- Templates ---
    TEMPLATES_DIR: str = "src/workers/templates"

    # --- ARQ Configuration ---
    arq_max_jobs: int = 10
    arq_job_timeout: int = 60
    arq_keep_result: int = 60

    # --- Redis (Internal field for ENV) ---
    redis_url_env: str | None = Field(default=None, alias="REDIS_URL")

    @property
    def arq_redis_settings(self):
        """
        Возвращает настройки Redis для arq.
        """
        from arq.connections import RedisSettings

        return RedisSettings(
            host=self.effective_redis_host,
            port=self.redis_port,
            password=self.redis_password,
        )
