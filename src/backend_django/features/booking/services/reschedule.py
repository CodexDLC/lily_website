"""Service for handling appointment reschedule tokens via Redis."""

import json
import secrets
from datetime import timedelta
from typing import TypedDict

from core.logger import log
from django.core.cache import caches

# We use the 'default' cache, which should be configured to use Redis in settings
cache = caches["default"]

TOKEN_PREFIX = "reschedule_token:"  # nosec B105
TOKEN_TTL_HOURS = 24


class TokenData(TypedDict):
    """Data stored in the reschedule token."""

    appointment_id: int
    proposed_slot: str  # The human-readable or datetime string of the proposed time


class RescheduleTokenService:
    """Manages secure tokens for appointment rescheduling."""

    @staticmethod
    def create_token(appointment_id: int, proposed_slot: str) -> str:
        """
        Generates a secure token and stores it in Redis with a 24-hour TTL.

        Args:
            appointment_id: The ID of the generic/proposed appointment.
            proposed_slot: String representation of the proposed time.

        Returns:
            The generated token string.
        """
        log.debug(f"Creating reschedule token for appointment {appointment_id}, slot: {proposed_slot}")

        token = secrets.token_urlsafe(32)
        key = f"{TOKEN_PREFIX}{token}"

        data: TokenData = {
            "appointment_id": appointment_id,
            "proposed_slot": proposed_slot,
        }

        # Store as JSON string. TTL = 24 hours.
        try:
            cache.set(key, json.dumps(data), timeout=int(timedelta(hours=TOKEN_TTL_HOURS).total_seconds()))
            log.info(f"Successfully created reschedule token for appointment {appointment_id}")
        except Exception as e:
            log.error(f"Failed to store reschedule token in Redis for appointment {appointment_id}: {e}")
            raise

        return token

    @staticmethod
    def get_token_data(token: str) -> TokenData | None:
        """
        Retrieves the data associated with a token.

        Args:
            token: The token string to look up.

        Returns:
            Dictionary with appointment details, or None if token is invalid/expired.
        """
        log.debug(f"Retrieving reschedule token data for token: {token[:8]}...")
        key = f"{TOKEN_PREFIX}{token}"

        try:
            raw_data = cache.get(key)
        except Exception as e:
            log.error(f"Redis error while retrieving token {token[:8]}: {e}")
            return None

        if not raw_data:
            log.warning(f"Reschedule token {token[:8]} not found or expired")
            return None

        try:
            data = json.loads(raw_data)
            log.debug(f"Token data retrieved: appointment_id={data.get('appointment_id')}")
            return data
        except json.JSONDecodeError as e:
            log.error(f"Failed to decode JSON for token {token[:8]}: {e}")
            return None

    @staticmethod
    def delete_token(token: str) -> None:
        """
        Deletes the token from Redis after it is successfully used.

        Args:
            token: The token string to delete.
        """
        log.debug(f"Deleting used reschedule token: {token[:8]}...")
        key = f"{TOKEN_PREFIX}{token}"
        try:
            cache.delete(key)
            log.info(f"Successfully deleted reschedule token {token[:8]}")
        except Exception as e:
            log.error(f"Failed to delete reschedule token {token[:8]} from Redis: {e}")
