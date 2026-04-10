from typing import Any

from core.logger import log
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
        log.debug(f"Retrieving booking state from session: {self.SESSION_KEY}")
        raw_data = self.session.get(self.SESSION_KEY, {})
        state = BookingState.from_dict(raw_data)
        log.debug(f"Current booking state: step={state.step}, service={state.service_id}, date={state.selected_date}")
        return state

    def save_state(self, state: BookingState):
        """Saves state object to session."""
        log.debug(f"Saving booking state to session: step={state.step}, service={state.service_id}")
        self.session[self.SESSION_KEY] = state.to_dict()
        self.session.modified = True
        log.info(f"Booking state saved successfully (Step {state.step})")

    def update_from_request(self, params: dict[str, Any], save: bool = True) -> "BookingState":
        """Updates state from GET/POST parameters."""
        log.debug(f"Updating booking state from request params: {params}")
        state = self.get_state()
        updated = False

        # Mapping request params to State fields
        if "step" in params:
            try:
                state.step = int(params["step"])
                updated = True
                log.debug(f"Updated step to {state.step}")
            except (ValueError, TypeError):
                log.warning(f"Invalid step value in request: {params.get('step')}")

        if "category" in params:
            state.category_slug = params["category"]
            updated = True
            log.debug(f"Updated category_slug to {state.category_slug}")

        if "service_id" in params:
            try:
                state.service_id = int(params["service_id"])
                updated = True
                log.debug(f"Updated service_id to {state.service_id}")
            except (ValueError, TypeError):
                log.warning(f"Invalid service_id value in request: {params.get('service_id')}")

        if "master_id" in params:
            state.master_id = params["master_id"]
            updated = True
            log.debug(f"Updated master_id to {state.master_id}")

        if "date" in params:
            from datetime import datetime

            try:
                state.selected_date = datetime.strptime(params["date"], "%Y-%m-%d").date()
                updated = True
                log.debug(f"Updated selected_date to {state.selected_date}")
            except (ValueError, TypeError):
                log.warning(f"Invalid date format in request: {params.get('date')}")

        if "time" in params:
            state.selected_time = params["time"]
            updated = True
            log.debug(f"Updated selected_time to {state.selected_time}")

        if updated and save:
            self.save_state(state)
        elif not updated:
            log.debug("No valid updates found in request params")
        return state

    def clear(self) -> None:
        """Clears booking data from session."""
        log.debug(f"Clearing booking session: {self.SESSION_KEY}")
        if self.SESSION_KEY in self.session:
            del self.session[self.SESSION_KEY]
            self.session.modified = True
            log.info("Booking session cleared successfully")
        else:
            log.debug("No booking session found to clear")
