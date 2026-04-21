import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.lily_backend.core.arq.client import DjangoArqClient


@pytest.mark.unit
class TestDjangoArqClient:
    def setup_method(self):
        # Reset class variables
        DjangoArqClient._pool = None
        DjangoArqClient._pool_loop = None

    @pytest.mark.asyncio
    @patch("src.lily_backend.core.arq.client.create_pool")
    @patch("src.lily_backend.core.arq.client.RedisSettings")
    @patch("src.lily_backend.core.arq.client.settings")
    async def test_get_pool_initialization(self, mock_settings, mock_redis_settings, mock_create_pool):
        """Test getting pool initializes it with correct settings."""
        mock_settings.ARQ_REDIS_URL = "redis://test:6379/1"
        mock_pool = MagicMock()
        mock_create_pool.return_value = mock_pool
        mock_redis_settings.from_dsn.return_value = MagicMock()

        pool = await DjangoArqClient.get_pool()

        assert pool == mock_pool
        mock_create_pool.assert_called_once()
        assert DjangoArqClient._pool == mock_pool
        assert DjangoArqClient._pool_loop == asyncio.get_running_loop()

    def test_job_id_helper(self):
        """Test _job_id static method."""
        assert DjangoArqClient._job_id(None) is None
        assert DjangoArqClient._job_id("simple_id") == "simple_id"

        mock_job = MagicMock()
        mock_job.job_id = "object_id"
        assert DjangoArqClient._job_id(mock_job) == "object_id"

    @pytest.mark.asyncio
    @patch.object(DjangoArqClient, "get_pool", new_callable=AsyncMock)
    async def test_enqueue_job(self, mock_get_pool):
        """Test enqueue_job calls pool's enqueue_job."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        await DjangoArqClient.enqueue_job("test_func", 1, 2, k=3)

        mock_pool.enqueue_job.assert_called_with("test_func", 1, 2, k=3)

    @pytest.mark.asyncio
    @patch.object(DjangoArqClient, "enqueue_job", new_callable=AsyncMock)
    async def test_aenqueue_converts_payload(self, mock_enqueue_job):
        """Test aenqueue formats arguments for enqueue_job."""
        mock_enqueue_job.return_value = "job_123"

        res = await DjangoArqClient.aenqueue("task", payload={"a": 1}, queue_name="q", defer_by=10, job_id="ji")

        assert res == "job_123"
        mock_enqueue_job.assert_called_with("task", payload={"a": 1}, _queue_name="q", _defer_by=10, _job_id="ji")

    @patch.object(DjangoArqClient, "aenqueue", new_callable=AsyncMock)
    def test_enqueue_sync_wrapper(self, mock_aenqueue):
        """Test sync enqueue wrapper."""
        mock_aenqueue.return_value = "sync_job"

        res = DjangoArqClient.enqueue("task", {"data": 1}, queue_name="high")

        assert res == "sync_job"
        # Since it uses async_to_sync, the call happens in a thread/loop
        mock_aenqueue.assert_called_with("task", {"data": 1}, queue_name="high")
