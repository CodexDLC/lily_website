import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.workers.notification_worker.dependencies import (
    init_notification_service,
    init_seven_io_service,
    init_twilio_service,
    init_orchestrator,
    init_arq_service,
    close_arq_service
)

@pytest.mark.asyncio
@patch("src.workers.notification_worker.dependencies.BaseArqService")
async def test_init_arq_service(mock_arq_cls):
    ctx = {}
    settings = MagicMock()
    mock_instance = mock_arq_cls.return_value
    mock_instance.init = AsyncMock()
    
    await init_arq_service(ctx, settings)
    
    assert "arq_service" in ctx
    mock_instance.init.assert_called_once()

@pytest.mark.asyncio
async def test_init_arq_service_error():
    with patch("src.workers.notification_worker.dependencies.BaseArqService", side_effect=Exception("Redis fail")):
        ctx = {}
        with pytest.raises(Exception, match="Redis fail"):
            await init_arq_service(ctx, MagicMock())

@pytest.mark.asyncio
async def test_close_arq_service():
    mock_arq = AsyncMock()
    ctx = {"arq_service": mock_arq}
    await close_arq_service(ctx, MagicMock())
    mock_arq.close.assert_called_once()

@pytest.mark.asyncio
async def test_init_notification_service():
    ctx = {
        "site_settings": MagicMock(
            site_base_url="http://site",
            logo_url="http://logo",
            smtp_host="smtp",
            smtp_port=587,
            smtp_user="user",
            smtp_password="pass",
            smtp_from_email="f@f.com",
            smtp_use_tls=True,
            sendgrid_api_key="SG",
            url_path_confirm="/",
            url_path_cancel="/",
            url_path_reschedule="/",
            url_path_contact_form="/"
        )
    }
    settings = MagicMock()
    settings.TEMPLATES_DIR = "/tmp"
    
    await init_notification_service(ctx, settings)
    assert "notification_service" in ctx

@pytest.mark.asyncio
async def test_init_seven_io_service():
    settings = MagicMock(SEVEN_IO_API_KEY="KEY")
    ctx = {}
    await init_seven_io_service(ctx, settings)
    assert ctx["seven_io_client"] is not None

@pytest.mark.asyncio
async def test_init_seven_io_service_missing():
    settings = MagicMock(SEVEN_IO_API_KEY=None)
    ctx = {}
    await init_seven_io_service(ctx, settings)
    assert ctx["seven_io_client"] is None

@pytest.mark.asyncio
async def test_init_twilio_service():
    settings = MagicMock(
        TWILIO_ACCOUNT_SID="AC123",
        TWILIO_AUTH_TOKEN="TOKEN",
        TWILIO_PHONE_NUMBER="+123",
        SENDGRID_API_KEY="SG"
    )
    ctx = {}
    await init_twilio_service(ctx, settings)
    assert ctx["twilio_service"] is not None

@pytest.mark.asyncio
async def test_init_twilio_service_missing():
    settings = MagicMock(TWILIO_ACCOUNT_SID=None)
    ctx = {}
    await init_twilio_service(ctx, settings)
    assert ctx["twilio_service"] is None

@pytest.mark.asyncio
async def test_init_orchestrator():
    ctx = {
        "notification_service": MagicMock(email_client=MagicMock()),
        "seven_io_client": MagicMock(),
        "twilio_service": MagicMock(),
    }
    await init_orchestrator(ctx, MagicMock())
    assert "orchestrator" in ctx
