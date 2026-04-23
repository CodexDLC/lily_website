from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio import Redis

from src.telegram_bot.core.config import BotSettings
from src.telegram_bot.core.factory import build_bot, compile_locales


def test_compile_locales_source_not_found(tmp_path):
    # Test with non-existent path
    base_path = tmp_path / "non_existent"
    result_path = compile_locales(base_path)
    assert "bot_locales" in result_path
    assert "{locale}" in result_path


def test_compile_locales_success(tmp_path):
    # Prepare mock structure
    locales_dir = tmp_path / "locales"
    en_dir = locales_dir / "en"
    en_dir.mkdir(parents=True)
    (en_dir / "test.ftl").write_text("key = value", encoding="utf-8")

    with patch("tempfile.gettempdir", return_value=str(tmp_path)):
        result_path = compile_locales(locales_dir)

        compiled_file = tmp_path / "bot_locales" / "en" / "messages.ftl"
        assert result_path == str(tmp_path / "bot_locales" / "{locale}")
        assert compiled_file.exists()
        content = compiled_file.read_text(encoding="utf-8")
        assert "key = value" in content


@pytest.fixture
def mock_redis():
    mock = MagicMock(spec=Redis)
    mock.ping = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_build_bot_success(mock_redis):
    settings = BotSettings(bot_token="123:ABC", secret_key="secret")

    with (
        patch("src.telegram_bot.core.factory.I18nMiddleware"),
        patch("src.telegram_bot.core.factory.compile_locales", return_value="mock_path"),
    ):
        bot, dp, i18n = await build_bot(settings, mock_redis)

        assert bot.token == "123:ABC"
        assert dp is not None
        mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
async def test_build_bot_no_token(mock_redis):
    settings = BotSettings(bot_token="", secret_key="secret")
    with pytest.raises(RuntimeError, match="BOT_TOKEN не найден"):
        await build_bot(settings, mock_redis)
