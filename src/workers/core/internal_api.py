from __future__ import annotations

from typing import Any

import httpx


class InternalApiClient:
    """Small scoped-token client for worker -> Django internal APIs."""

    def __init__(self, *, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def open(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def post(
        self, path: str, *, scope: str, token: str | None, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not token:
            raise RuntimeError(f"Missing internal API token for scope '{scope}'")
        await self.open()
        assert self._client is not None
        response = await self._client.post(
            path,
            headers={
                "X-Internal-Scope": scope,
                "X-Internal-Token": token,
            },
            json=json or {},
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {"result": payload}
