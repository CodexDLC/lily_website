"""
codexn_tools.booking.modes
==========================
Operating modes for the booking engine.

Imports:
    from codexn_tools.booking import BookingMode
"""

from enum import StrEnum


class BookingMode(StrEnum):
    """
    Operating mode for ChainFinder.

    SINGLE_DAY:
        All services from the request must fit within a single day.
        The engine searches for a continuous (or with allowed gaps) chain of slots.
        The most common mode — client wants multiple services in one visit.

    MULTI_DAY:
        Each service can be scheduled for a different day.
        Stub — to be implemented in the next iteration.
        Running find() with this mode will return EngineResult(solutions=[]).

    MASTER_LOCKED:
        Booking for a specific professional (e.g., from their personal profile page).
        Works like SINGLE_DAY, but ServiceRequest.possible_master_ids
        contains exactly one id — the chosen professional's id.
        The engine relies entirely on the provided master constraints.

    Example:
        mode = BookingMode.SINGLE_DAY
        mode = BookingMode("single_day")   # string cast works too
    """

    SINGLE_DAY = "single_day"
    MULTI_DAY = "multi_day"
    MASTER_LOCKED = "master_locked"
