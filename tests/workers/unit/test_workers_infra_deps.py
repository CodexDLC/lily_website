import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.workers.core.base_module.dependencies import init_common_dependencies, close_common_dependencies
from src.workers.core.config import WorkerSettings
from src.workers.core.site_settings import WorkerSiteSettings

@pytest.fixture
def mock_settings():
    settings = MagicMock(spec=WorkerSettings)
    settings.redis_url = "redis://localhost:6379/0"
    settings.redis_site_settings_project = "lily"
    settings.redis_site_settings_key = "settings"
    settings.backend_api_base_url = "http://backend"
    settings.internal_api_timeout = 10
    
    # SMTP Fallbacks
    settings.SMTP_HOST = "smtp.test"
    settings.SMTP_PORT = 587
    settings.SMTP_USER = "user"
    settings.SMTP_PASSWORD = "pass"
    settings.SMTP_FROM_EMAIL = "from@test"
    settings.SMTP_USE_TLS = True
    settings.SMTP_USE_SSL = False
    settings.SENDGRID_API_KEY = "sg_key"
    return settings

@pytest.mark.asyncio
async def test_init_common_dependencies(mock_settings):
    ctx = {}
    
    # Mock global dependencies
    with patch("src.workers.core.base_module.dependencies.from_url") as mock_from_url, \
         patch("src.workers.core.base_module.dependencies.SiteSettingsRedisReader") as mock_reader_cls, \
         patch("src.workers.core.base_module.dependencies.InternalApiClient") as mock_api_cls:
        
        # Setup mocks
        mock_redis = MagicMock()
        mock_from_url.return_value = mock_redis
        
        mock_reader = AsyncMock()
        mock_reader.load.return_value = WorkerSiteSettings(company_name="Lily")
        mock_reader_cls.return_value = mock_reader
        
        mock_api = AsyncMock()
        mock_api_cls.return_value = mock_api
        
        # Execute
        await init_common_dependencies(ctx, mock_settings)
        
        # Assert
        assert "redis_client" in ctx
        assert "redis_service" in ctx
        assert "internal_api" in ctx
        assert "site_settings" in ctx
        mock_api.open.assert_awaited_once()
        mock_reader.load.assert_awaited_once()

@pytest.mark.asyncio
async def test_close_common_dependencies(mock_settings):
    mock_api = AsyncMock()
    mock_redis = AsyncMock()
    ctx = {
        "internal_api": mock_api,
        "redis_client": mock_redis
    }
    
    # Execute
    await close_common_dependencies(ctx, mock_settings)
    
    # Assert
    mock_api.close.assert_awaited_once()
    mock_redis.close.assert_awaited_once()

@pytest.mark.asyncio
async def test_close_common_dependencies_partial(mock_settings):
    ctx = {} # Empty context
    
    # Execute - should not raise exception
    await close_common_dependencies(ctx, mock_settings)
