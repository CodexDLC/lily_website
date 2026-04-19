"""
Unit tests for codex_tools.booking.exceptions.
Covers all exception classes and their message-building logic.
"""

from datetime import date

import pytest
from codex_tools.booking.exceptions import (
    BookingEngineError,
    ChainBuildError,
    InvalidBookingDateError,
    InvalidServiceDurationError,
    MasterNotAvailableError,
    NoAvailabilityError,
    SlotAlreadyBookedError,
)


@pytest.mark.unit
class TestBookingEngineError:
    def test_default_message(self):
        exc = BookingEngineError()
        assert str(exc) == "Booking system error"

    def test_custom_message(self):
        exc = BookingEngineError("Custom error")
        assert str(exc) == "Custom error"

    def test_is_exception_subclass(self):
        assert issubclass(BookingEngineError, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(BookingEngineError, match="Booking system error"):
            raise BookingEngineError()


@pytest.mark.unit
class TestNoAvailabilityError:
    def test_default_message_no_args(self):
        exc = NoAvailabilityError()
        assert "no available slots" in str(exc).lower()
        assert exc.booking_date is None
        assert exc.service_ids == []

    def test_with_booking_date(self):
        d = date(2024, 5, 10)
        exc = NoAvailabilityError(booking_date=d)
        assert "10.05.2024" in str(exc)
        assert exc.booking_date == d

    def test_with_service_ids(self):
        exc = NoAvailabilityError(service_ids=["5", "12"])
        assert exc.service_ids == ["5", "12"]

    def test_with_custom_message_overrides_date(self):
        d = date(2024, 5, 10)
        exc = NoAvailabilityError(booking_date=d, message="Override message")
        assert str(exc) == "Override message"

    def test_with_date_and_service_ids(self):
        d = date(2024, 6, 15)
        exc = NoAvailabilityError(booking_date=d, service_ids=["1"])
        assert "15.06.2024" in str(exc)
        assert exc.service_ids == ["1"]

    def test_service_ids_defaults_to_empty_list(self):
        exc = NoAvailabilityError()
        assert exc.service_ids == []

    def test_is_booking_engine_error_subclass(self):
        assert issubclass(NoAvailabilityError, BookingEngineError)

    def test_date_format_dd_mm_yyyy(self):
        d = date(2024, 1, 5)
        exc = NoAvailabilityError(booking_date=d)
        assert "05.01.2024" in str(exc)


@pytest.mark.unit
class TestInvalidServiceDurationError:
    def test_default_message_no_args(self):
        exc = InvalidServiceDurationError()
        assert "Incorrect service duration" in str(exc)
        assert exc.service_id is None
        assert exc.duration_minutes is None

    def test_with_service_id_and_duration(self):
        exc = InvalidServiceDurationError(service_id="5", duration_minutes=0)
        msg = str(exc)
        assert "Service 5" in msg
        assert "0 min" in msg

    def test_with_custom_message(self):
        exc = InvalidServiceDurationError(message="Custom duration error")
        assert str(exc) == "Custom duration error"

    def test_service_id_only_uses_default(self):
        # When only service_id is given but not duration_minutes, uses default message
        exc = InvalidServiceDurationError(service_id="7")
        assert exc.service_id == "7"
        assert exc.duration_minutes is None
        # Falls through to default_message
        assert "Incorrect service duration" in str(exc)

    def test_duration_only_uses_default(self):
        exc = InvalidServiceDurationError(duration_minutes=0)
        assert exc.duration_minutes == 0
        assert "Incorrect service duration" in str(exc)

    def test_is_booking_engine_error_subclass(self):
        assert issubclass(InvalidServiceDurationError, BookingEngineError)

    def test_negative_duration_message(self):
        exc = InvalidServiceDurationError(service_id="3", duration_minutes=-5)
        assert "Service 3" in str(exc)
        assert "-5 min" in str(exc)


@pytest.mark.unit
class TestInvalidBookingDateError:
    def test_default_message(self):
        exc = InvalidBookingDateError()
        assert "unavailable for booking" in str(exc)
        assert exc.booking_date is None
        assert exc.reason is None

    def test_with_date_only(self):
        d = date(2020, 1, 1)
        exc = InvalidBookingDateError(booking_date=d)
        assert "01.01.2020" in str(exc)
        assert exc.reason is None

    def test_with_date_and_reason(self):
        d = date(2020, 1, 1)
        exc = InvalidBookingDateError(booking_date=d, reason="Date in the past")
        msg = str(exc)
        assert "01.01.2020" in msg
        assert "Date in the past" in msg

    def test_with_custom_message(self):
        exc = InvalidBookingDateError(message="Override")
        assert str(exc) == "Override"

    def test_custom_message_overrides_date_and_reason(self):
        d = date(2024, 5, 10)
        exc = InvalidBookingDateError(booking_date=d, reason="closed", message="Custom msg")
        assert str(exc) == "Custom msg"

    def test_is_booking_engine_error_subclass(self):
        assert issubclass(InvalidBookingDateError, BookingEngineError)

    def test_reason_only_uses_default(self):
        exc = InvalidBookingDateError(reason="closed")
        # No date given, falls to default_message
        assert "unavailable for booking" in str(exc)


@pytest.mark.unit
class TestSlotAlreadyBookedError:
    def test_default_message(self):
        exc = SlotAlreadyBookedError()
        assert "selected slot was booked" in str(exc)
        assert exc.master_id is None
        assert exc.service_id is None
        assert exc.booking_date is None
        assert exc.slot_time is None

    def test_with_slot_time_and_date(self):
        d = date(2024, 5, 10)
        exc = SlotAlreadyBookedError(slot_time="14:00", booking_date=d)
        msg = str(exc)
        assert "14:00" in msg
        assert "10.05.2024" in msg

    def test_with_all_fields(self):
        d = date(2024, 5, 10)
        exc = SlotAlreadyBookedError(master_id="3", service_id="5", booking_date=d, slot_time="14:00")
        assert exc.master_id == "3"
        assert exc.service_id == "5"
        assert "14:00" in str(exc)

    def test_with_custom_message(self):
        exc = SlotAlreadyBookedError(message="Custom slot error")
        assert str(exc) == "Custom slot error"

    def test_slot_time_only_uses_default(self):
        exc = SlotAlreadyBookedError(slot_time="10:00")
        # No date given, falls to default
        assert "selected slot was booked" in str(exc)

    def test_date_only_uses_default(self):
        exc = SlotAlreadyBookedError(booking_date=date(2024, 5, 10))
        # No slot_time given, falls to default
        assert "selected slot was booked" in str(exc)

    def test_is_booking_engine_error_subclass(self):
        assert issubclass(SlotAlreadyBookedError, BookingEngineError)


@pytest.mark.unit
class TestChainBuildError:
    def test_default_message(self):
        exc = ChainBuildError()
        assert "Could not find a schedule" in str(exc)
        assert exc.failed_at_index is None
        assert exc.reason is None

    def test_with_reason(self):
        exc = ChainBuildError(reason="max_chain_duration exceeded")
        assert "max_chain_duration exceeded" in str(exc)
        assert "Could not assemble the chain" in str(exc)

    def test_with_failed_at_index_and_reason(self):
        exc = ChainBuildError(failed_at_index=2, reason="incompatible services")
        assert exc.failed_at_index == 2
        assert "incompatible services" in str(exc)

    def test_with_custom_message(self):
        exc = ChainBuildError(message="Custom chain error")
        assert str(exc) == "Custom chain error"

    def test_failed_at_index_only_uses_default(self):
        exc = ChainBuildError(failed_at_index=3)
        # No reason given, uses default_message
        assert "Could not find a schedule" in str(exc)

    def test_is_booking_engine_error_subclass(self):
        assert issubclass(ChainBuildError, BookingEngineError)


@pytest.mark.unit
class TestMasterNotAvailableError:
    def test_default_message(self):
        exc = MasterNotAvailableError()
        assert "unavailable on this date" in str(exc)
        assert exc.master_id is None
        assert exc.booking_date is None

    def test_with_booking_date(self):
        d = date(2024, 5, 10)
        exc = MasterNotAvailableError(booking_date=d)
        assert "10.05.2024" in str(exc)

    def test_with_master_id_and_date(self):
        d = date(2024, 5, 10)
        exc = MasterNotAvailableError(master_id="3", booking_date=d)
        assert exc.master_id == "3"
        assert "10.05.2024" in str(exc)

    def test_with_custom_message(self):
        exc = MasterNotAvailableError(message="Master on holiday")
        assert str(exc) == "Master on holiday"

    def test_master_id_only_uses_default(self):
        exc = MasterNotAvailableError(master_id="5")
        # No date, uses default_message
        assert "unavailable on this date" in str(exc)

    def test_is_booking_engine_error_subclass(self):
        assert issubclass(MasterNotAvailableError, BookingEngineError)

    def test_date_format(self):
        d = date(2024, 12, 31)
        exc = MasterNotAvailableError(booking_date=d)
        assert "31.12.2024" in str(exc)


@pytest.mark.unit
class TestExceptionHierarchy:
    """All custom exceptions must be catchable as BookingEngineError."""

    def test_no_availability_caught_as_base(self):
        with pytest.raises(BookingEngineError):
            raise NoAvailabilityError()

    def test_invalid_duration_caught_as_base(self):
        with pytest.raises(BookingEngineError):
            raise InvalidServiceDurationError()

    def test_invalid_date_caught_as_base(self):
        with pytest.raises(BookingEngineError):
            raise InvalidBookingDateError()

    def test_slot_booked_caught_as_base(self):
        with pytest.raises(BookingEngineError):
            raise SlotAlreadyBookedError()

    def test_chain_build_caught_as_base(self):
        with pytest.raises(BookingEngineError):
            raise ChainBuildError()

    def test_master_not_available_caught_as_base(self):
        with pytest.raises(BookingEngineError):
            raise MasterNotAvailableError()
