from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import Dispatcher

from src.telegram_bot.app_telegram import shutdown, startup
from src.telegram_bot.core.config import BotSettings


@pytest.fixture
def settings():
    return BotSettings(bot_token="test", secret_key="test", api_url="http://api")  # pragma: allowlist secret


@pytest.mark.asyncio
async def test_startup(settings):
    with patch("src.telegram_bot.app_telegram.setup_logging") as mock_log:
        await startup(settings)
        mock_log.assert_called_once_with(settings, service_name="telegram_bot")


@pytest.mark.asyncio
async def test_shutdown():
    mock_container = AsyncMock()
    await shutdown(mock_container)
    mock_container.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_main_flow_mocked():
    # We don't run the full main because it starts polling,
    # but we can test the initialization parts by mocking them.
    from src.telegram_bot.app_telegram import main

    with (
        patch("src.telegram_bot.app_telegram.BotSettings"),
        patch("src.telegram_bot.app_telegram.startup", new_callable=AsyncMock),
        patch("src.telegram_bot.app_telegram.Redis.from_url"),
        patch("src.telegram_bot.app_telegram.BotContainer") as mock_container_cls,
        patch(
            "src.telegram_bot.app_telegram.build_bot",
            new_callable=AsyncMock,
            return_value=(MagicMock(), MagicMock(spec=Dispatcher)),
        ) as mock_build_bot,
        patch("src.telegram_bot.app_telegram.build_main_router"),
        patch("src.telegram_bot.app_telegram.attach_middlewares") as mock_attach_middlewares,
    ):
        # Mock container and its stream_processor
        mock_container = mock_container_cls.return_value
        mock_container.stream_processor.start_listening = AsyncMock()
        mock_container.init_arq = AsyncMock()
        mock_container.shutdown = AsyncMock()

        # We need to break the loop or mock start_polling to raise an exception
        # Use a custom exception instead of KeyboardInterrupt to avoid killing the whole test runner
        class StopPollingError(Exception):
            pass

        _, mock_dp = await mock_build_bot()
        mock_dp.start_polling = AsyncMock(side_effect=StopPollingError)

        with pytest.raises(StopPollingError):
            await main()

        mock_attach_middlewares.assert_called_once()
