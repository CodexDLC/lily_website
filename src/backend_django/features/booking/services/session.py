from typing import Any

from django.http import HttpRequest
from features.booking.dto import BookingState


class BookingSessionService:
    """
    Manages booking wizard state in Django session using BookingState DTO.
    """

    SESSION_KEY = "booking_wizard_v1"

    def __init__(self, request: HttpRequest):
        self.session = request.session

    def get_state(self) -> BookingState:
        """Returns typed state object."""
        raw_data = self.session.get(self.SESSION_KEY, {})
        return BookingState.from_dict(raw_data)

    def save_state(self, state: BookingState):
        """Saves state object to session."""
        self.session[self.SESSION_KEY] = state.to_dict()
        self.session.modified = True

    def update_from_request(self, params: dict[str, Any]):
        """Updates state from GET/POST parameters."""
        state = self.get_state()
        updated = False

        # Mapping request params to State fields
        if "step" in params:
            try:
                state.step = int(params["step"])
                updated = True
            except (ValueError, TypeError):
                pass

        if "category" in params:
            state.category_slug = params["category"]
            updated = True

        if "service_id" in params:
            try:
                state.service_id = int(params["service_id"])
                updated = True
            except (ValueError, TypeError):
                pass

        if "master_id" in params:
            state.master_id = params["master_id"]
            updated = True

        if "date" in params:
            # Date parsing is handled here or we store string temporarily?
            # The DTO expects 'selected_date' as date object.
            # But params come as string "YYYY-MM-DD".
            # Let's parse it here to keep DTO clean or use a helper.
            # Actually, DTO from_dict handles parsing, but here we are setting attribute directly.
            from datetime import datetime

            try:
                state.selected_date = datetime.strptime(params["date"], "%Y-%m-%d").date()
                updated = True
            except (ValueError, TypeError):
                pass

        if "time" in params:
            state.selected_time = params["time"]
            updated = True

        if updated:
            self.save_state(state)

    def clear(self) -> None:
        """Clears booking data from session."""
        if self.SESSION_KEY in self.session:
            del self.session[self.SESSION_KEY]
            self.session.modified = True
