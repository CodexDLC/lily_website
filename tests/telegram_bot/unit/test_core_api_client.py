from unittest.mock import MagicMock, patch

import httpx
import pytest

from src.telegram_bot.core.api_client import ApiClientError, BaseApiClient


class TestBaseApiClient:
    @pytest.mark.asyncio
    @patch("src.telegram_bot.core.api_client.httpx.AsyncClient")
    async def test_request_success(self, mock_client_class):
        # Setup mock client
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_client.request.return_value = mock_response

        client = BaseApiClient(base_url="http://test-api", api_key="test-key", timeout=5.0)
        result = await client._request("GET", "/test/", params={"a": 1})

        assert result == {"status": "ok"}
        mock_client.request.assert_called_once_with(
            method="GET",
            url="http://test-api/test/",
            headers={"Content-Type": "application/json", "Accept": "application/json", "X-API-Key": "test-key"},
            json=None,
            params={"a": 1},
        )

    @pytest.mark.asyncio
    @patch("src.telegram_bot.core.api_client.httpx.AsyncClient")
    async def test_request_http_error(self, mock_client_class):
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Error", request=MagicMock(), response=mock_response
        )
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client.request.return_value = mock_response

        client = BaseApiClient(base_url="http://test-api")
        with pytest.raises(ApiClientError, match="HTTP Error: 404"):
            await client._request("GET", "/fail/")

    @pytest.mark.asyncio
    @patch("src.telegram_bot.core.api_client.httpx.AsyncClient")
    async def test_request_connection_error(self, mock_client_class):
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.request.side_effect = httpx.RequestError("Conn Failed")

        client = BaseApiClient(base_url="http://test-api")
        with pytest.raises(ApiClientError, match="Connection Error"):
            await client._request("GET", "/fail/")
