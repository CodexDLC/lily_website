"""
Unit tests for codex_tools.booking.validators.BookingValidator.
Pure logic tests — no Django ORM required.
"""

from datetime import datetime

import pytest
from codex_tools.booking.dto import SingleServiceSolution
from codex_tools.booking.validators import BookingValidator


def _dt(hour: int, minute: int = 0) -> datetime:
    """Helper: naive datetime on 2024-05-10 at given hour:minute."""
    return datetime(2024, 5, 10, hour, minute)


def _make_solution(
    master_id: str,
    start_hour: int,
    start_min: int,
    end_hour: int,
    end_min: int,
    gap_end_hour: int | None = None,
    gap_end_min: int = 0,
    service_id: str = "svc1",
) -> SingleServiceSolution:
    start = _dt(start_hour, start_min)
    end = _dt(end_hour, end_min)
    gap_end = _dt(gap_end_hour, gap_end_min) if gap_end_hour is not None else end
    return SingleServiceSolution(
        service_id=service_id,
        master_id=master_id,
        start_time=start,
        end_time=end,
        gap_end_time=gap_end,
    )


@pytest.mark.unit
class TestBookingValidatorIsSlotFree:
    def setup_method(self):
        self.validator = BookingValidator()

    def test_slot_free_with_no_busy_intervals(self):
        result = self.validator.is_slot_free(
            slot_start=_dt(10),
            slot_end=_dt(11),
            busy_intervals=[],
        )
        assert result is True

    def test_slot_overlaps_busy_interval(self):
        # Slot 10:30–11:30 overlaps with busy 10:00–11:00
        result = self.validator.is_slot_free(
            slot_start=_dt(10, 30),
            slot_end=_dt(11, 30),
            busy_intervals=[(_dt(10, 0), _dt(11, 0))],
        )
        assert result is False

    def test_slot_free_adjacent_after_busy(self):
        # Slot 11:00–12:00 is adjacent to busy 10:00–11:00 (no overlap)
        result = self.validator.is_slot_free(
            slot_start=_dt(11, 0),
            slot_end=_dt(12, 0),
            busy_intervals=[(_dt(10, 0), _dt(11, 0))],
        )
        assert result is True

    def test_slot_free_adjacent_before_busy(self):
        # Slot 09:00–10:00 adjacent to busy 10:00–11:00
        result = self.validator.is_slot_free(
            slot_start=_dt(9, 0),
            slot_end=_dt(10, 0),
            busy_intervals=[(_dt(10, 0), _dt(11, 0))],
        )
        assert result is True

    def test_slot_completely_inside_busy(self):
        # Slot 10:15–10:45 fully inside busy 10:00–11:00
        result = self.validator.is_slot_free(
            slot_start=_dt(10, 15),
            slot_end=_dt(10, 45),
            busy_intervals=[(_dt(10, 0), _dt(11, 0))],
        )
        assert result is False

    def test_slot_spans_entire_busy_period(self):
        # Slot 09:00–12:00 completely wraps busy 10:00–11:00
        result = self.validator.is_slot_free(
            slot_start=_dt(9, 0),
            slot_end=_dt(12, 0),
            busy_intervals=[(_dt(10, 0), _dt(11, 0))],
        )
        assert result is False

    def test_slot_free_with_multiple_busy_intervals(self):
        # Slot 12:00–13:00 free from all busy
        result = self.validator.is_slot_free(
            slot_start=_dt(12, 0),
            slot_end=_dt(13, 0),
            busy_intervals=[
                (_dt(9, 0), _dt(10, 0)),
                (_dt(10, 30), _dt(11, 30)),
            ],
        )
        assert result is True

    def test_slot_conflicts_with_second_busy_interval(self):
        # Slot 11:00–12:00 conflicts with second busy 10:30–11:30
        result = self.validator.is_slot_free(
            slot_start=_dt(11, 0),
            slot_end=_dt(12, 0),
            busy_intervals=[
                (_dt(9, 0), _dt(10, 0)),
                (_dt(10, 30), _dt(11, 30)),
            ],
        )
        assert result is False

    def test_same_start_as_busy_is_conflict(self):
        # Slot starts exactly when busy starts
        result = self.validator.is_slot_free(
            slot_start=_dt(10, 0),
            slot_end=_dt(11, 0),
            busy_intervals=[(_dt(10, 0), _dt(11, 0))],
        )
        assert result is False


@pytest.mark.unit
class TestBookingValidatorNoConflicts:
    def setup_method(self):
        self.validator = BookingValidator()

    def test_empty_solutions_no_conflict(self):
        assert self.validator.no_conflicts([]) is True

    def test_single_solution_no_conflict(self):
        sol = _make_solution("m1", 9, 0, 10, 0)
        assert self.validator.no_conflicts([sol]) is True

    def test_two_solutions_different_masters_no_conflict(self):
        sol1 = _make_solution("m1", 9, 0, 10, 0)
        sol2 = _make_solution("m2", 9, 0, 10, 0)
        assert self.validator.no_conflicts([sol1, sol2]) is True

    def test_two_solutions_same_master_adjacent_no_conflict(self):
        # Master m1: 09:00–10:00 then 10:00–11:00 (adjacent)
        sol1 = _make_solution("m1", 9, 0, 10, 0, gap_end_hour=10, gap_end_min=0)
        sol2 = _make_solution("m1", 10, 0, 11, 0, service_id="svc2")
        assert self.validator.no_conflicts([sol1, sol2]) is True

    def test_two_solutions_same_master_overlapping_conflict(self):
        # Master m1: 09:00–10:10 (gap_end=10:10) and 10:00–11:00 (conflict)
        sol1 = _make_solution("m1", 9, 0, 10, 0, gap_end_hour=10, gap_end_min=10)
        sol2 = _make_solution("m1", 10, 0, 11, 0, service_id="svc2")
        # sol2.start_time(10:00) < sol1.gap_end_time(10:10) → conflict
        assert self.validator.no_conflicts([sol1, sol2]) is False

    def test_three_solutions_same_master_sequential_no_conflict(self):
        sol1 = _make_solution("m1", 9, 0, 10, 0, gap_end_hour=10)
        sol2 = _make_solution("m1", 10, 0, 11, 0, gap_end_hour=11, service_id="svc2")
        sol3 = _make_solution("m1", 11, 0, 12, 0, gap_end_hour=12, service_id="svc3")
        assert self.validator.no_conflicts([sol1, sol2, sol3]) is True

    def test_unsorted_solutions_handled_correctly(self):
        # Pass in reverse order — validator should sort by start_time
        sol1 = _make_solution("m1", 10, 0, 11, 0, gap_end_hour=11, service_id="svc2")
        sol2 = _make_solution("m1", 9, 0, 10, 0, gap_end_hour=10)
        assert self.validator.no_conflicts([sol1, sol2]) is True

    def test_mixed_masters_with_conflict_in_one(self):
        # m1 has conflict, m2 is fine
        sol_m1_a = _make_solution("m1", 9, 0, 10, 0, gap_end_hour=10, gap_end_min=30)
        sol_m1_b = _make_solution("m1", 10, 0, 11, 0, service_id="svc2")  # starts before gap_end
        sol_m2 = _make_solution("m2", 9, 0, 10, 0)
        assert self.validator.no_conflicts([sol_m1_a, sol_m1_b, sol_m2]) is False


@pytest.mark.unit
class TestBookingValidatorSolutionFitsInWindows:
    def setup_method(self):
        self.validator = BookingValidator()

    def test_fits_perfectly_in_window(self):
        sol = _make_solution("m1", 10, 0, 11, 0, gap_end_hour=11)
        windows = [(_dt(9, 0), _dt(12, 0))]
        assert self.validator.solution_fits_in_windows(sol, windows) is True

    def test_does_not_fit_outside_window(self):
        # Solution 10:00–11:00 but window is 11:00–12:00
        sol = _make_solution("m1", 10, 0, 11, 0, gap_end_hour=11)
        windows = [(_dt(11, 0), _dt(12, 0))]
        assert self.validator.solution_fits_in_windows(sol, windows) is False

    def test_fits_in_second_window(self):
        sol = _make_solution("m1", 14, 0, 15, 0, gap_end_hour=15)
        windows = [(_dt(9, 0), _dt(12, 0)), (_dt(13, 0), _dt(17, 0))]
        assert self.validator.solution_fits_in_windows(sol, windows) is True

    def test_does_not_fit_when_no_windows(self):
        sol = _make_solution("m1", 10, 0, 11, 0, gap_end_hour=11)
        assert self.validator.solution_fits_in_windows(sol, []) is False

    def test_does_not_fit_when_gap_end_exceeds_window(self):
        # Solution: start=10:00, gap_end=12:30 but window ends at 12:00
        sol = _make_solution("m1", 10, 0, 12, 0, gap_end_hour=12, gap_end_min=30)
        windows = [(_dt(9, 0), _dt(12, 0))]
        assert self.validator.solution_fits_in_windows(sol, windows) is False

    def test_fits_exactly_at_window_boundaries(self):
        # Solution start == window start, gap_end == window end
        sol = _make_solution("m1", 9, 0, 12, 0, gap_end_hour=12)
        windows = [(_dt(9, 0), _dt(12, 0))]
        assert self.validator.solution_fits_in_windows(sol, windows) is True
