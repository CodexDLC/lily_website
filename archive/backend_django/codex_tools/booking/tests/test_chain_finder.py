"""
Unit tests for ChainFinder (backtracking engine).

No Django, no DB -- pure Python.
Run: pytest features/booking/tests/engine/test_chain_finder.py -v
"""

from datetime import date, datetime, timedelta

from codex_tools.booking.chain_finder import ChainFinder
from codex_tools.booking.dto import (
    BookingEngineRequest,
    MasterAvailability,
    ServiceRequest,
)
from codex_tools.booking.modes import BookingMode


def dt(h: int, m: int = 0) -> datetime:
    """Helper: create datetime on fixed date 2024-05-10."""
    return datetime(2024, 5, 10, h, m)


def make_availability(
    master_id: str,
    windows: list[tuple[datetime, datetime]],
    buffer: int = 0,
) -> MasterAvailability:
    return MasterAvailability(
        master_id=master_id,
        free_windows=windows,
        buffer_between_minutes=buffer,
    )


def make_request(
    services: list[tuple[str, int, list[str], int]],  # (id, duration, masters, gap)
    mode: BookingMode = BookingMode.SINGLE_DAY,
) -> BookingEngineRequest:
    return BookingEngineRequest(
        service_requests=[
            ServiceRequest(
                service_id=svc_id,
                duration_minutes=duration,
                possible_master_ids=masters,
                min_gap_after_minutes=gap,
            )
            for svc_id, duration, masters, gap in services
        ],
        booking_date=date(2024, 5, 10),
        mode=mode,
    )


class TestChainFinderSingleService:
    """Single service -- basic happy path tests."""

    def setup_method(self):
        self.finder = ChainFinder(step_minutes=30)

    def test_finds_slots_in_free_window(self):
        """One master, one service -- should find multiple slots."""
        request = make_request([("5", 60, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(12))])}

        result = self.finder.find(request, avail)

        assert result.has_solutions
        # 9:00, 9:30, 10:00 -- 10:30+60=11:30 < 12:00 also fits
        assert len(result.solutions) >= 3

    def test_no_solutions_when_window_too_small(self):
        """Window smaller than service duration -- no solutions."""
        request = make_request([("5", 120, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(10))])}

        result = self.finder.find(request, avail)

        assert not result.has_solutions

    def test_multiple_masters_all_contribute(self):
        """Two masters available -- solutions from both."""
        request = make_request([("5", 60, ["1", "2"], 0)])
        avail = {
            "1": make_availability("1", [(dt(9), dt(12))]),
            "2": make_availability("2", [(dt(14), dt(17))]),
        }

        result = self.finder.find(request, avail)

        master_ids = {item.master_id for sol in result.solutions for item in sol.items}
        assert "1" in master_ids
        assert "2" in master_ids

    def test_sorted_by_start_time(self):
        """Solutions should be sorted by start time (earliest first)."""
        request = make_request([("5", 60, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail)

        start_times = [s.starts_at for s in result.solutions]
        assert start_times == sorted(start_times)

    def test_max_solutions_limit(self):
        """max_solutions cap is respected."""
        request = make_request([("5", 30, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail, max_solutions=5)

        assert len(result.solutions) <= 5

    def test_get_unique_start_times(self):
        """get_unique_start_times returns sorted HH:MM strings."""
        request = make_request([("5", 60, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(12))])}

        result = self.finder.find(request, avail)
        times = result.get_unique_start_times()

        assert all(":" in t for t in times)
        assert times == sorted(times)


class TestChainFinderTwoServices:
    """Two services -- chain booking tests."""

    def setup_method(self):
        self.finder = ChainFinder(step_minutes=30)

    def test_two_services_same_master(self):
        """Two services for the same master -- no overlap."""
        request = make_request(
            [
                ("svc_a", 60, ["1"], 0),
                ("svc_b", 60, ["1"], 0),
            ]
        )
        avail = {"1": make_availability("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail)

        assert result.has_solutions
        for sol in result.solutions:
            items = sorted(sol.items, key=lambda i: i.start_time)
            # Second service must start after first ends
            assert items[1].start_time >= items[0].end_time

    def test_gap_after_service_respected(self):
        """min_gap_after_minutes=30 -- next service starts 30min after first ends."""
        request = make_request(
            [
                ("svc_a", 60, ["1"], 30),  # 60min + 30min gap
                ("svc_b", 60, ["1"], 0),
            ]
        )
        avail = {"1": make_availability("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail)

        assert result.has_solutions
        for sol in result.solutions:
            items = sorted(sol.items, key=lambda i: i.start_time)
            gap_required = timedelta(minutes=60 + 30)
            assert items[1].start_time >= items[0].start_time + gap_required

    def test_two_services_different_masters(self):
        """Two services each with different masters -- parallel booking."""
        request = make_request(
            [
                ("svc_a", 60, ["1"], 0),
                ("svc_b", 60, ["2"], 0),
            ]
        )
        avail = {
            "1": make_availability("1", [(dt(9), dt(18))]),
            "2": make_availability("2", [(dt(9), dt(18))]),
        }

        result = self.finder.find(request, avail)

        assert result.has_solutions
        # Services can even start at the same time (different masters)
        for sol in result.solutions:
            master_ids = {item.master_id for item in sol.items}
            assert "1" in master_ids
            assert "2" in master_ids

    def test_no_solutions_second_service_can_not_fit(self):
        """Day too short for 2 services + gap."""
        request = make_request(
            [
                ("svc_a", 60, ["1"], 60),  # 60min service + 60min gap
                ("svc_b", 60, ["1"], 0),  # another 60min
            ]
        )
        # Window only 2 hours -- need 3h total
        avail = {"1": make_availability("1", [(dt(9), dt(11))])}

        result = self.finder.find(request, avail)

        assert not result.has_solutions


class TestChainFinderBuffer:
    """Buffer between clients tests."""

    def setup_method(self):
        self.finder = ChainFinder(step_minutes=30)

    def test_buffer_between_clients_respected(self):
        """Master with 15min buffer -- next client starts at least 15min after prev ends."""
        request = make_request(
            [
                ("svc_a", 60, ["1"], 0),
                ("svc_b", 60, ["1"], 0),
            ]
        )
        avail = {"1": make_availability("1", [(dt(9), dt(18))], buffer=15)}

        result = self.finder.find(request, avail)

        assert result.has_solutions
        for sol in result.solutions:
            items = sorted(sol.items, key=lambda i: i.start_time)
            min_gap = timedelta(minutes=60 + 15)  # service + buffer
            assert items[1].start_time >= items[0].start_time + min_gap


class TestChainFinderMinStart:
    """min_start (global advance booking constraint) tests."""

    def test_min_start_filters_past_slots(self):
        """Slots before min_start are excluded."""
        # min_start = 10:45 -- slots at 9:00, 9:30, 10:00, 10:30 excluded
        finder = ChainFinder(step_minutes=30, min_start=dt(10, 45))
        request = make_request([("5", 60, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(18))])}

        result = finder.find(request, avail)

        assert result.has_solutions
        # First slot must be >= 11:00 (aligned to grid, >= 10:45)
        assert result.best.starts_at >= dt(11, 0)


class TestEngineResult:
    """Tests for EngineResult properties."""

    def test_best_is_earliest(self):
        """result.best returns the solution with earliest start."""
        finder = ChainFinder(step_minutes=30)
        request = make_request([("5", 60, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(18))])}

        result = finder.find(request, avail)

        assert result.best is not None
        assert result.best.starts_at == min(s.starts_at for s in result.solutions)

    def test_to_display_format(self):
        """to_display() returns dict with service_id keys and HH:MM times."""
        finder = ChainFinder(step_minutes=30)
        request = make_request([("svc_42", 60, ["1"], 0)])
        avail = {"1": make_availability("1", [(dt(9), dt(18))])}

        result = finder.find(request, avail)
        display = result.best.to_display()

        assert "svc_42" in display
        assert "start" in display["svc_42"]
        assert ":" in display["svc_42"]["start"]
