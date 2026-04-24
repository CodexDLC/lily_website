"""
Root conftest for the entire pytest suite.

Provides cross-domain fixtures (fakeredis, freezegun helpers, httpx mocking)
that are not tied to any single feature. Per-domain fixtures live in:

  - tests/lily_backend/conftest.py  (Django ORM fixtures)
  - tests/workers/conftest.py       (arq/worker fixtures)
  - tests/e2e/conftest.py           (live docker stack fixtures)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from fakeredis.aioredis import FakeRedis as FakeAsyncRedis


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip @pytest.mark.e2e tests unless `-m e2e` is explicitly requested."""
    mark_expr = config.getoption("-m") or ""
    if "e2e" in mark_expr:
        return
    skip_e2e = pytest.mark.skip(reason="e2e test — run with `pytest -m e2e`")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


# ---------------------------------------------------------------------------
# Redis — fakeredis shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_async_redis() -> FakeAsyncRedis:
    """Async FakeRedis instance; isolated per test."""
    from fakeredis.aioredis import FakeRedis

    return FakeRedis(decode_responses=True)


@pytest.fixture
def fake_sync_redis():
    """Sync FakeRedis instance; isolated per test."""
    import fakeredis

    return fakeredis.FakeRedis(decode_responses=True)
