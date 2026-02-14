from pathlib import Path

from src.shared.core.config import CommonSettings


class WorkerSettings(CommonSettings):
    """
    Настройки для воркеров.
    Наследует общие настройки (Redis, Logging) из shared.
    Добавляет специфичные для воркеров параметры, если нужно.
    """

    # Настройки ARQ (можно переопределить через ENV)
    arq_max_jobs: int = 20
    arq_job_timeout: int = 60
    arq_keep_result: int = 5

    # Путь к папке с шаблонами относительно корня проекта
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent / "templates"

    # Настройки SMTP для отправки email (перенесены из EmailSettings)
    SMTP_HOST: str = "smtp.spacemail.com"
    SMTP_PORT: int = 465  # Изменено на 465
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_USE_TLS: bool = False  # Изменено на False
