from codex_tools.common.arq_client import BaseArqClient
from django.conf import settings


class DjangoArqClient:
    """
    Project-specific ARQ Client.
    Initializes the universal BaseArqClient with Django settings.
    """

    _instance = None

    @classmethod
    def _get_instance(cls):
        if cls._instance is None:
            cls._instance = BaseArqClient(
                redis_host=settings.REDIS_HOST, redis_port=settings.REDIS_PORT, redis_password=settings.REDIS_PASSWORD
            )
        return cls._instance

    @classmethod
    def enqueue_job(cls, function: str, *args, **kwargs):
        return cls._get_instance().enqueue_job(function, *args, **kwargs)

    @classmethod
    async def enqueue_job_async(cls, function: str, *args, **kwargs):
        return await cls._get_instance().enqueue_job_async(function, *args, **kwargs)
