"""
Unit tests for SlotCalculator.

No Django, no DB -- pure Python.
Run: pytest features/booking/tests/engine/test_slot_calculator.py -v
"""

from datetime import datetime

import pytest
from codex_tools.booking.slot_calculator import SlotCalculator


def dt(h: int, m: int = 0) -> datetime:
    """Helper: create datetime on fixed date 2024-05-10."""
    return datetime(2024, 5, 10, h, m)


class TestFindSlotsInWindow:
    """Tests for SlotCalculator.find_slots_in_window()."""

    def setup_method(self):
        self.calc = SlotCalculator(step_minutes=30)

    def test_basic_window_returns_correct_slots(self):
        """Window 9:00-12:00, service 60min, step 30min: 5 slots (9:00..11:00)."""
        slots = self.calc.find_slots_in_window(window_start=dt(9), window_end=dt(12), duration_minutes=60)
        # 9:00+60=10:00 ✓  9:30+60=10:30 ✓  10:00+60=11:00 ✓
        # 10:30+60=11:30 ✓  11:00+60=12:00 ✓  11:30+60=12:30 ✗
        assert slots == [dt(9, 0), dt(9, 30), dt(10, 0), dt(10, 30), dt(11, 0)]

    def test_service_exactly_fills_window(self):
        """Window 9:00-10:00, service 60min: only 9:00 slot."""
        slots = self.calc.find_slots_in_window(window_start=dt(9), window_end=dt(10), duration_minutes=60)
        assert slots == [dt(9, 0)]

    def test_service_too_long_for_window(self):
        """Window 9:00-9:30, service 60min: no slots."""
        slots = self.calc.find_slots_in_window(window_start=dt(9), window_end=dt(9, 30), duration_minutes=60)
        assert slots == []

    def test_min_start_cuts_early_slots(self):
        """min_start=9:40 with step 30min: first slot should be 10:00."""
        slots = self.calc.find_slots_in_window(
            window_start=dt(9),
            window_end=dt(12),
            duration_minutes=60,
            min_start=dt(9, 40),
        )
        assert slots[0] == dt(10, 0)
        assert dt(9, 0) not in slots
        assert dt(9, 30) not in slots

    def test_min_start_exactly_on_grid(self):
        """min_start exactly on grid boundary -- that slot is included."""
        slots = self.calc.find_slots_in_window(
            window_start=dt(9),
            window_end=dt(12),
            duration_minutes=30,
            min_start=dt(9, 30),
        )
        assert dt(9, 30) in slots
        assert dt(9, 0) not in slots

    def test_step_15_minutes(self):
        """15-minute step produces twice as many slots."""
        calc15 = SlotCalculator(step_minutes=15)
        slots = calc15.find_slots_in_window(window_start=dt(9), window_end=dt(10), duration_minutes=30)
        # 9:00, 9:15, 9:30 -- 9:45 + 30min = 10:15 > 10:00, excluded
        assert slots == [dt(9, 0), dt(9, 15), dt(9, 30)]

    def test_invalid_step_raises(self):
        with pytest.raises(ValueError):
            SlotCalculator(step_minutes=0)


class TestMergeFreeWindows:
    """Tests for SlotCalculator.merge_free_windows()."""

    def setup_method(self):
        self.calc = SlotCalculator(step_minutes=30)

    def test_no_busy_returns_full_day(self):
        """No appointments -- full work day is free."""
        windows = self.calc.merge_free_windows(work_start=dt(9), work_end=dt(18), busy_intervals=[])
        assert windows == [(dt(9), dt(18))]

    def test_single_appointment_splits_day(self):
        """One appointment 10:00-11:00 splits day into 2 windows."""
        windows = self.calc.merge_free_windows(
            work_start=dt(9),
            work_end=dt(18),
            busy_intervals=[(dt(10), dt(11))],
        )
        assert windows == [(dt(9), dt(10)), (dt(11), dt(18))]

    def test_buffer_extends_busy_interval(self):
        """Buffer 10 min after appointment: busy until 11:10, not 11:00."""
        windows = self.calc.merge_free_windows(
            work_start=dt(9),
            work_end=dt(18),
            busy_intervals=[(dt(10), dt(11))],
            buffer_minutes=10,
        )
        assert windows == [(dt(9), dt(10)), (dt(11, 10), dt(18))]

    def test_break_cuts_window(self):
        """Lunch break 13:00-14:00 creates separate afternoon window."""
        windows = self.calc.merge_free_windows(
            work_start=dt(9),
            work_end=dt(18),
            busy_intervals=[],
            break_interval=(dt(13), dt(14)),
        )
        assert windows == [(dt(9), dt(13)), (dt(14), dt(18))]

    def test_appointment_and_break_combined(self):
        """Appointment 10:00-11:00 + break 13:00-14:00 creates 3 windows."""
        windows = self.calc.merge_free_windows(
            work_start=dt(9),
            work_end=dt(18),
            busy_intervals=[(dt(10), dt(11))],
            break_interval=(dt(13), dt(14)),
        )
        assert windows == [
            (dt(9), dt(10)),
            (dt(11), dt(13)),
            (dt(14), dt(18)),
        ]

    def test_appointment_fills_entire_day(self):
        """If appointment covers whole day -- no free windows."""
        windows = self.calc.merge_free_windows(
            work_start=dt(9),
            work_end=dt(18),
            busy_intervals=[(dt(9), dt(18))],
        )
        assert windows == []

    def test_overlapping_appointments_merged(self):
        """Overlapping appointments are merged before computing free windows."""
        windows = self.calc.merge_free_windows(
            work_start=dt(9),
            work_end=dt(18),
            busy_intervals=[
                (dt(10), dt(12)),
                (dt(11), dt(13)),  # overlaps with previous
            ],
        )
        # Merged busy: 10:00-13:00 -> free: 9:00-10:00 and 13:00-18:00
        assert windows == [(dt(9), dt(10)), (dt(13), dt(18))]
