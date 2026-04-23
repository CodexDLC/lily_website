"""Redis manager for temporary action tokens (e.g. rescheduling confirmation)."""

import json
import secrets
from datetime import timedelta
from typing import Any, TypedDict

from codex_django.core.redis.managers.base import BaseDjangoRedisManager


class ActionTokenData(TypedDict):
    """Schema for data stored in action tokens."""

    appointment_id: int
    proposed_slot: str  # ISO datetime or human-readable slot
    action_type: str  # e.g. 'reschedule', 'cancel'


class ActionTokenRedisManager(BaseDjangoRedisManager):
    """
    Manages temporary session-like tokens for booking actions.
    Ported and adapted from legacy RescheduleTokenService.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(prefix="auth:action", **kwargs)

    def create_token(
        self, appointment_id: int, proposed_slot: str, action_type: str = "reschedule", ttl_hours: int = 24
    ) -> str:
        """
        Creates a secure token and stores action data in Redis.
        """
        token = secrets.token_urlsafe(32)
        key = self.make_key(token)

        data: ActionTokenData = {
            "appointment_id": appointment_id,
            "proposed_slot": proposed_slot,
            "action_type": action_type,
        }

        # Using codex-platform synchronous operation pattern for type-safe Redis interactions.
        with self.sync_string() as redis:
            redis.set(key, json.dumps(data), ttl=int(timedelta(hours=ttl_hours).total_seconds()))
        return token

    def get_token_data(self, token: str) -> ActionTokenData | None:
        """
        Retrieves and decodes token data if it exists.
        """
        key = self.make_key(token)
        with self.sync_string() as redis:
            raw_data = redis.get(key)

        if not raw_data:
            return None

        try:
            return json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            return None

    def delete_token(self, token: str) -> None:
        """
        Removes the token after successful use.
        """
        key = self.make_key(token)
        with self.sync_string() as redis:
            redis.delete(key)
