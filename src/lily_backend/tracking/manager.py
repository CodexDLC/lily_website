from __future__ import annotations

from django.conf import settings

_TTL = 60 * 60 * 24 * 30  # 30 days

"""
TrackingRedisManager — uses django_redis connection (sync)
"""


def _redis():
    try:
        import django_redis

        alias = getattr(settings, "CABINET_TRACKING", {}).get("redis_alias", "default")
        return django_redis.get_redis_connection(alias)
    except (NotImplementedError, Exception):
        return None


def _prefix() -> str:
    from django.conf import settings as s

    name = getattr(s, "PROJECT_NAME", "")
    return f"{name}:tracking" if name else "tracking"


class TrackingRedisManager:
    def _daily_key(self, date_str: str) -> str:
        return f"{_prefix()}:daily:{date_str}"

    def _uniq_key(self, date_str: str) -> str:
        return f"{_prefix()}:uniq:{date_str}"

    # ── Write ────────────────────────────────────────────────────────────────

    def record(self, path: str, date_str: str, user_id: str | None) -> None:
        r = _redis()
        if r is None:
            return  # no Redis in local dev — skip silently
        pipe = r.pipeline(transaction=False)
        pipe.hincrby(self._daily_key(date_str), path, 1)
        pipe.expire(self._daily_key(date_str), _TTL)
        if user_id:
            pipe.pfadd(self._uniq_key(date_str), user_id)
            pipe.expire(self._uniq_key(date_str), _TTL)
        pipe.execute()

    # ── Read ─────────────────────────────────────────────────────────────────

    def get_daily(self, date_str: str) -> dict[str, str] | None:
        r = _redis()
        if r is None:
            return None
        raw = r.hgetall(self._daily_key(date_str))
        return {k.decode(): v.decode() for k, v in raw.items()} if raw else None

    def get_unique_count(self, date_str: str) -> int:
        r = _redis()
        if r is None:
            return 0
        return int(r.pfcount(self._uniq_key(date_str)))

    def get_multi_day(self, dates: list[str]) -> list[dict[str, str] | None]:
        r = _redis()
        if r is None:
            return [None] * len(dates)
        pipe = r.pipeline(transaction=False)
        for d in dates:
            pipe.hgetall(self._daily_key(d))
        results = pipe.execute()
        return [{k.decode(): v.decode() for k, v in snap.items()} if snap else None for snap in results]


_manager = TrackingRedisManager()


def get_tracking_manager() -> TrackingRedisManager:
    return _manager
