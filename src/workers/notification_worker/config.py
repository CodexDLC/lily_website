from pathlib import Path

from src.workers.core.config import WorkerSettings as BaseWorkerSettings


class WorkerSettings(BaseWorkerSettings):
    """
    Настройки Notification Worker.
    Наследуемся от базовых настроек воркера (src/workers/core/config.py),
    которые уже включают Redis, SMTP, Twilio и ARQ.
    """

    # Paths
    # Переопределяем TEMPLATES_DIR, чтобы использовать Path (в базовом это str)
    # и указывать на правильную папку относительно этого файла.
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    TEMPLATES_DIR: str = str(Path(__file__).resolve().parent.parent / "templates")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = WorkerSettings()
