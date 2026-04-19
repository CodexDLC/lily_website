from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workers.core.internal_api import InternalApiClient


@pytest.fixture
def client():
    return InternalApiClient(base_url="https://api.test")


class TestInternalApiClient:
    @pytest.mark.asyncio
    async def test_post_success(self, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.post("/v1/test", scope="test", token="secret", json={"foo": "bar"})

            assert result == {"status": "ok"}
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == "/v1/test"
            assert kwargs["headers"]["X-Internal-Scope"] == "test"
            assert kwargs["headers"]["X-Internal-Token"] == "secret"
            assert kwargs["json"] == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test_post_missing_token(self, client):
        with pytest.raises(RuntimeError, match="Missing internal API token"):
            await client.post("/v1/test", scope="test", token=None)

    @pytest.mark.asyncio
    async def test_close(self, client):
        with patch("httpx.AsyncClient.aclose", new_callable=AsyncMock) as mock_close:
            await client.open()  # Initialize client
            await client.close()
            mock_close.assert_called_once()
            assert client._client is None
