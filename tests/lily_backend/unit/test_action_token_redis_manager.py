import json
from contextlib import contextmanager

from system.redis import ActionTokenRedisManager


class FakeStringOperations:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}
        self.deleted: list[str] = []

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        self.values[key] = value
        self.ttls[key] = ttl

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.values.pop(key, None)


def test_action_token_manager_uses_sync_string_contract(monkeypatch):
    ops = FakeStringOperations()

    @contextmanager
    def fake_sync_string(self):
        yield ops

    monkeypatch.setattr(ActionTokenRedisManager, "sync_string", fake_sync_string)
    monkeypatch.setattr("system.redis.secrets.token_urlsafe", lambda _size: "fixed-token")

    manager = ActionTokenRedisManager()

    token = manager.create_token(appointment_id=42, proposed_slot="2026-04-18T10:00:00", ttl_hours=2)
    key = manager.make_key("fixed-token")

    assert token == "fixed-token"
    assert ops.ttls[key] == 7200
    assert json.loads(ops.values[key]) == {
        "appointment_id": 42,
        "proposed_slot": "2026-04-18T10:00:00",
        "action_type": "reschedule",
    }
    assert manager.get_token_data(token) == {
        "appointment_id": 42,
        "proposed_slot": "2026-04-18T10:00:00",
        "action_type": "reschedule",
    }

    manager.delete_token(token)

    assert ops.deleted == [key]
    assert manager.get_token_data(token) is None
