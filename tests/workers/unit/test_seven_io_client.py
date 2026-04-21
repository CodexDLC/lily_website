import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.workers.core.base_module.seven_io_client import SevenIOClient

@pytest.fixture
def seven_io_client():
    return SevenIOClient(api_key="seven_key", from_name="LILY")

@pytest.mark.asyncio
async def test_send_sms_success(seven_io_client):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"success": "100"}
        
        res = await seven_io_client.send_sms("123456", "Hello")
        assert res is True
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_send_sms_failure_data(seven_io_client):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"success": "0"}
        
        res = await seven_io_client.send_sms("123456", "Hello")
        assert res is False

@pytest.mark.asyncio
async def test_send_sms_exception(seven_io_client):
    with patch("httpx.AsyncClient.post", side_effect=Exception("Network error")):
        res = await seven_io_client.send_sms("123456", "Hello")
        assert res is False

@pytest.mark.asyncio
async def test_send_whatsapp_success(seven_io_client):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"status": "success"}
        
        res = await seven_io_client.send_whatsapp("123456", "Hello")
        assert res is True

@pytest.mark.asyncio
async def test_send_whatsapp_failure(seven_io_client):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"status": "error"}
        
        res = await seven_io_client.send_whatsapp("123456", "Hello")
        assert res is False
