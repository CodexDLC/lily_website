"""Service for handling Action Tokens and Magic Links."""

from features.booking.models.appointment import Appointment

from system.redis import ActionTokenData, ActionTokenRedisManager


class AuthService:
    """
    High-level logic for authentication-related actions.
    """

    def __init__(self) -> None:
        self.redis_mgr = ActionTokenRedisManager()

    def generate_reschedule_link(self, appointment: Appointment, proposed_slot_iso: str) -> str:
        """
        Creates a reschedule token and returns the confirmation URL.
        """
        token = self.redis_mgr.create_token(
            appointment_id=appointment.id, proposed_slot=proposed_slot_iso, action_type="reschedule", ttl_hours=24
        )

        # We assume the view will be at /booking/reschedule/confirm/<token>/
        # relative_url = reverse("booking:reschedule_confirm", kwargs={"token": token})
        # For now, we return the path-like string until URLs are fully registered.
        return f"/booking/reschedule/confirm/{token}/"

    def verify_action_token(self, token: str) -> ActionTokenData | None:
        """
        Verifies if the token is valid and returns its data.
        """
        return self.redis_mgr.get_token_data(token)

    def consume_token(self, token: str) -> None:
        """
        Deletes the token after use.
        """
        self.redis_mgr.delete_token(token)
