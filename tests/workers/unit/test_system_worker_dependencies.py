from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.system_worker.dependencies import close_arq_service, init_arq_service


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.arq_redis_settings = {"host": "localhost", "port": 6379}
    return settings


@pytest.mark.asyncio
class TestSystemWorkerDependencies:
    @patch("src.workers.system_worker.dependencies.BaseArqService")
    async def test_init_arq_service(self, mock_arq_class, mock_settings):
        mock_arq_instance = AsyncMock()
        mock_arq_class.return_value = mock_arq_instance

        ctx = {}
        await init_arq_service(ctx, mock_settings)

        assert ctx["arq_service"] == mock_arq_instance
        mock_arq_instance.init.assert_called_once()
        mock_arq_class.assert_called_once_with(mock_settings.arq_redis_settings)

    async def test_close_arq_service(self, mock_settings):
        mock_arq_instance = AsyncMock()
        ctx = {"arq_service": mock_arq_instance}

        await close_arq_service(ctx, mock_settings)
        mock_arq_instance.close.assert_called_once()

    async def test_close_arq_service_missing(self, mock_settings):
        ctx = {}
        # Should not raise
        await close_arq_service(ctx, mock_settings)
