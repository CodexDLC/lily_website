from src.workers.core.config import WorkerSettings as BaseWorkerSettings


class WorkerSettings(BaseWorkerSettings):
    """Settings for system worker tasks."""


settings = WorkerSettings()
