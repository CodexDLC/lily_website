"""Compatibility wrapper for booking bridge access inside the sandbox cabinet."""

from codex_django.booking import (
    BookingActionResult,
    BookingBridge,
    BookingCalendarPrefillState,
    BookingFormFieldState,
    BookingFormState,
    BookingModalActionState,
    BookingModalState,
    BookingProfileState,
    BookingQuickCreateState,
    BookingSlotOptionState,
    BookingSlotPickerState,
    BookingSummaryItemState,
)
from features.booking.services.cabinet import get_booking_bridge

__all__ = [
    "BookingActionResult",
    "BookingBridge",
    "BookingCalendarPrefillState",
    "BookingFormFieldState",
    "BookingFormState",
    "BookingModalActionState",
    "BookingModalState",
    "BookingProfileState",
    "BookingQuickCreateState",
    "BookingSlotOptionState",
    "BookingSlotPickerState",
    "BookingSummaryItemState",
    "get_booking_bridge",
]
