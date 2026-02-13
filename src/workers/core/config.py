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
