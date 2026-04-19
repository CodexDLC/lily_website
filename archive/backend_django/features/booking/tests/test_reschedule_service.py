"""Tests for RescheduleTokenService."""

import pytest
from features.booking.services.reschedule import RescheduleTokenService


@pytest.mark.unit
class TestRescheduleTokenService:
    def test_create_and_retrieve_token(self):
        token = RescheduleTokenService.create_token(
            appointment_id=42,
            proposed_slot="25.12.2026 10:00",
        )
        assert token is not None
        assert len(token) > 10

        data = RescheduleTokenService.get_token_data(token)
        assert data is not None
        assert data["appointment_id"] == 42
        assert data["proposed_slot"] == "25.12.2026 10:00"

    def test_get_nonexistent_token_returns_none(self):
        result = RescheduleTokenService.get_token_data("totally-nonexistent-token-xyz")
        assert result is None

    def test_delete_token(self):
        token = RescheduleTokenService.create_token(appointment_id=1, proposed_slot="01.01.2027 09:00")
        RescheduleTokenService.delete_token(token)
        assert RescheduleTokenService.get_token_data(token) is None

    def test_token_is_unique_each_call(self):
        token1 = RescheduleTokenService.create_token(appointment_id=1, proposed_slot="slot1")
        token2 = RescheduleTokenService.create_token(appointment_id=1, proposed_slot="slot2")
        assert token1 != token2

    def test_delete_nonexistent_token_is_safe(self):
        # Should not raise
        RescheduleTokenService.delete_token("token-that-doesnt-exist")
