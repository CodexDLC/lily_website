from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio import Redis

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.core.container import BotContainer, _feature_names


def test_feature_names_utility():
    paths = ["features.telegram.menu", "features.telegram.commands"]
    assert _feature_names(paths, "telegram") == ["menu", "commands"]


@pytest.fixture
def mock_redis():
    return MagicMock(spec=Redis)


@pytest.fixture
def settings():
    return BotSettings(bot_token="test_token", secret_key="test_secret")  # pragma: allowlist secret


class TestBotContainer:
    def test_init_success(self, settings, mock_redis):
        # Mocking INSTALLED_FEATURES to avoid actual discovery during core init if possible
        # or just letting it run with empty lists
        with (
            patch("src.telegram_bot.core.container.INSTALLED_FEATURES", []),
            patch("src.telegram_bot.core.container.INSTALLED_REDIS_FEATURES", []),
        ):
            container = BotContainer(settings, mock_redis)

            assert container.redis is not None
            assert container.site_settings is not None
            assert container.url_signer is not None
            assert hasattr(container, "bot_menu")

    @pytest.mark.asyncio
    async def test_init_arq(self, settings, mock_redis):
        with patch("src.telegram_bot.core.container.create_pool", new_callable=AsyncMock) as mock_create_pool:
            container = BotContainer(settings, mock_redis)
            await container.init_arq()
            mock_create_pool.assert_called_once()
            assert container.arq_pool is not None

    def test_set_bot(self, settings, mock_redis):
        container = BotContainer(settings, mock_redis)
        mock_bot = MagicMock()

        container.set_bot(mock_bot)
        assert container.bot == mock_bot

    @pytest.mark.asyncio
    async def test_shutdown(self, settings, mock_redis):
        container = BotContainer(settings, mock_redis)
        container.stream_processor = AsyncMock()
        container.arq_pool = AsyncMock()
        container.redis_client = AsyncMock()

        await container.shutdown()

        container.stream_processor.stop_listening.assert_called_once()
        container.arq_pool.close.assert_called_once()
        container.redis_client.close.assert_called_once()
