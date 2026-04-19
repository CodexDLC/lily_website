"""
Unit tests for new engine features (v0.2.0).

No Django, no DB -- pure Python.
Run: pytest features/booking/engine/tests/test_new_features.py -v

Covers:
  - SlotCalculator.find_gaps()
  - SlotCalculator.split_window_by_service()
  - ChainFinder.find() with max_unique_starts
  - ChainFinder.find() with overlap_allowed=False
  - ChainFinder.find() with max_chain_duration_minutes
  - ChainFinder.find_nearest()
  - BookingScorer (preferred master, same master, compactness)
  - WaitlistEntry
"""

from datetime import date, datetime, timedelta

from codex_tools.booking.chain_finder import ChainFinder
from codex_tools.booking.dto import (
    BookingChainSolution,
    BookingEngineRequest,
    EngineResult,
    MasterAvailability,
    ServiceRequest,
    WaitlistEntry,
)
from codex_tools.booking.modes import BookingMode
from codex_tools.booking.scorer import BookingScorer, ScoringWeights
from codex_tools.booking.slot_calculator import SlotCalculator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def dt(h: int, m: int = 0, d: int = 10) -> datetime:
    """Helper: datetime on 2024-05-<d>."""
    return datetime(2024, 5, d, h, m)


def make_avail(mid: str, windows: list[tuple[datetime, datetime]], buf: int = 0) -> MasterAvailability:
    return MasterAvailability(master_id=mid, free_windows=windows, buffer_between_minutes=buf)


def make_request(
    services: list[tuple[str, int, list[str], int]],  # (id, dur, masters, gap)
    mode: BookingMode = BookingMode.SINGLE_DAY,
    overlap_allowed: bool = True,
    max_chain_duration_minutes: int | None = None,
    booking_date: date = date(2024, 5, 10),
) -> BookingEngineRequest:
    return BookingEngineRequest(
        service_requests=[
            ServiceRequest(
                service_id=sid,
                duration_minutes=dur,
                possible_master_ids=masters,
                min_gap_after_minutes=gap,
            )
            for sid, dur, masters, gap in services
        ],
        booking_date=booking_date,
        mode=mode,
        overlap_allowed=overlap_allowed,
        max_chain_duration_minutes=max_chain_duration_minutes,
    )


# ---------------------------------------------------------------------------
# SlotCalculator.find_gaps()
# ---------------------------------------------------------------------------


class TestFindGaps:
    def setup_method(self):
        self.calc = SlotCalculator(step_minutes=30)

    def test_returns_windows_above_min_gap(self):
        """Only windows >= min_gap_minutes are returned."""
        free = [(dt(9), dt(10)), (dt(11), dt(14)), (dt(16), dt(18))]
        gaps = self.calc.find_gaps(free, min_gap_minutes=90)

        # 9:00-10:00 = 60min → excluded
        # 11:00-14:00 = 180min → included
        # 16:00-18:00 = 120min → included
        assert len(gaps) == 2
        starts = [g[0] for g in gaps]
        assert dt(11) in starts
        assert dt(16) in starts

    def test_filters_short_windows(self):
        """Windows shorter than min_gap_minutes are excluded."""
        free = [(dt(9), dt(9, 30))]
        gaps = self.calc.find_gaps(free, min_gap_minutes=60)
        assert gaps == []

    def test_returns_duration_in_minutes(self):
        """Third element of each tuple is duration in minutes."""
        free = [(dt(9), dt(11))]  # 120 minutes
        gaps = self.calc.find_gaps(free, min_gap_minutes=60)
        assert gaps[0][2] == 120

    def test_empty_windows(self):
        """Empty input returns empty list."""
        assert self.calc.find_gaps([], 30) == []

    def test_sorted_by_start(self):
        """Result is sorted by window start time."""
        free = [(dt(14), dt(16)), (dt(9), dt(11))]
        gaps = self.calc.find_gaps(free, min_gap_minutes=60)
        assert gaps[0][0] == dt(9)
        assert gaps[1][0] == dt(14)

    def test_exact_boundary_included(self):
        """Window exactly at min_gap_minutes boundary is included."""
        free = [(dt(9), dt(10))]  # 60 min
        gaps = self.calc.find_gaps(free, min_gap_minutes=60)
        assert len(gaps) == 1


# ---------------------------------------------------------------------------
# SlotCalculator.split_window_by_service()
# ---------------------------------------------------------------------------


class TestSplitWindowByService:
    def setup_method(self):
        self.calc = SlotCalculator(step_minutes=30)

    def test_service_in_middle_creates_two_windows(self):
        """Service 11:00-12:00 in window 9:00-18:00 → two windows."""
        result = self.calc.split_window_by_service(
            window_start=dt(9),
            window_end=dt(18),
            service_start=dt(11),
            service_end=dt(12),
        )
        assert result == [(dt(9), dt(11)), (dt(12), dt(18))]

    def test_service_at_start_leaves_one_window(self):
        """Service at window start → only tail window."""
        result = self.calc.split_window_by_service(
            window_start=dt(9),
            window_end=dt(18),
            service_start=dt(9),
            service_end=dt(11),
        )
        assert result == [(dt(11), dt(18))]

    def test_service_at_end_leaves_one_window(self):
        """Service at window end → only head window."""
        result = self.calc.split_window_by_service(
            window_start=dt(9),
            window_end=dt(18),
            service_start=dt(16),
            service_end=dt(18),
        )
        assert result == [(dt(9), dt(16))]

    def test_service_fills_window_completely(self):
        """Service fills entire window → no remaining windows."""
        result = self.calc.split_window_by_service(
            window_start=dt(9),
            window_end=dt(18),
            service_start=dt(9),
            service_end=dt(18),
        )
        assert result == []


# ---------------------------------------------------------------------------
# ChainFinder.find() — max_unique_starts
# ---------------------------------------------------------------------------


class TestMaxUniqueStarts:
    def setup_method(self):
        self.finder = ChainFinder(step_minutes=30)

    def test_limits_unique_start_times(self):
        """max_unique_starts=3 → at most 3 distinct start times in solutions."""
        request = make_request([("5", 30, ["1"], 0)])
        avail = {"1": make_avail("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail, max_unique_starts=3)

        unique_starts = {s.starts_at for s in result.solutions}
        assert len(unique_starts) <= 3

    def test_max_unique_starts_one(self):
        """max_unique_starts=1 → only earliest start time returned."""
        request = make_request([("5", 30, ["1", "2"], 0)])
        avail = {
            "1": make_avail("1", [(dt(9), dt(18))]),
            "2": make_avail("2", [(dt(9), dt(18))]),
        }

        result = self.finder.find(request, avail, max_unique_starts=1)

        unique_starts = {s.starts_at for s in result.solutions}
        assert len(unique_starts) == 1

    def test_no_limit_when_none(self):
        """None means no limit — many starts returned."""
        request = make_request([("5", 30, ["1"], 0)])
        avail = {"1": make_avail("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail, max_unique_starts=None)

        assert len({s.starts_at for s in result.solutions}) > 3


# ---------------------------------------------------------------------------
# ChainFinder.find() — overlap_allowed=False
# ---------------------------------------------------------------------------


class TestOverlapAllowed:
    def setup_method(self):
        self.finder = ChainFinder(step_minutes=30)

    def test_overlap_false_services_sequential(self):
        """overlap_allowed=False: each service starts after all previous end."""
        request = make_request(
            [("svc_a", 60, ["1"], 0), ("svc_b", 60, ["2"], 0)],
            overlap_allowed=False,
        )
        avail = {
            "1": make_avail("1", [(dt(9), dt(18))]),
            "2": make_avail("2", [(dt(9), dt(18))]),
        }

        result = self.finder.find(request, avail)

        assert result.has_solutions
        for sol in result.solutions:
            items = sorted(sol.items, key=lambda i: i.start_time)
            assert items[1].start_time >= items[0].end_time, (
                f"Overlap! svc_b starts {items[1].start_time} before svc_a ends {items[0].end_time}"
            )

    def test_overlap_true_allows_parallel(self):
        """overlap_allowed=True (default): different masters can work simultaneously."""
        request = make_request(
            [("svc_a", 60, ["1"], 0), ("svc_b", 60, ["2"], 0)],
            overlap_allowed=True,
        )
        avail = {
            "1": make_avail("1", [(dt(9), dt(18))]),
            "2": make_avail("2", [(dt(9), dt(18))]),
        }

        result = self.finder.find(request, avail)

        # At least one solution where both start at the same time
        parallel_solutions = [
            sol
            for sol in result.solutions
            if len({item.start_time for item in sol.items}) == 1  # all start at same time
        ]
        assert len(parallel_solutions) > 0


# ---------------------------------------------------------------------------
# ChainFinder.find() — max_chain_duration_minutes
# ---------------------------------------------------------------------------


class TestMaxChainDuration:
    def setup_method(self):
        self.finder = ChainFinder(step_minutes=30)

    def test_prunes_chains_exceeding_max_duration(self):
        """max_chain_duration_minutes=90: chains > 90min span are excluded."""
        # Two 60-min services sequentially = 120min span → exceeds 90min limit
        request = make_request(
            [("svc_a", 60, ["1"], 0), ("svc_b", 60, ["1"], 0)],
            max_chain_duration_minutes=90,
        )
        avail = {"1": make_avail("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail)

        # Should find no solutions: 60+60=120 > 90 for same master sequential
        # OR solutions where masters are different and overlap collapses span to 60min
        # Since we only have master "1", both services must be sequential → 120min span → pruned
        assert not result.has_solutions

    def test_allows_chains_within_max_duration(self):
        """max_chain_duration_minutes=180: 120min chain is allowed."""
        request = make_request(
            [("svc_a", 60, ["1"], 0), ("svc_b", 60, ["1"], 0)],
            max_chain_duration_minutes=180,
        )
        avail = {"1": make_avail("1", [(dt(9), dt(18))])}

        result = self.finder.find(request, avail)

        assert result.has_solutions
        for sol in result.solutions:
            assert sol.span_minutes <= 180


# ---------------------------------------------------------------------------
# ChainFinder.find_nearest()
# ---------------------------------------------------------------------------


class TestFindNearest:
    def setup_method(self):
        self.finder = ChainFinder(step_minutes=30)

    def test_finds_first_available_date(self):
        """find_nearest() returns result for first date with availability."""
        request = make_request([("5", 60, ["1"], 0)])

        # No availability on day 10, available on day 12
        def get_avail(d: date) -> dict[str, MasterAvailability]:
            if d == date(2024, 5, 12):
                return {"1": make_avail("1", [(datetime(2024, 5, 12, 9), datetime(2024, 5, 12, 18))])}
            return {}

        result = self.finder.find_nearest(
            request=request,
            get_availability_for_date=get_avail,
            search_from=date(2024, 5, 10),
            search_days=30,
        )

        assert result.has_solutions
        # All solutions should be on the 12th
        for sol in result.solutions:
            assert sol.starts_at.day == 12

    def test_returns_empty_when_nothing_found(self):
        """find_nearest() returns empty EngineResult if no days have availability."""
        request = make_request([("5", 60, ["1"], 0)])

        def get_avail(d: date) -> dict[str, MasterAvailability]:
            return {}  # always empty

        result = self.finder.find_nearest(
            request=request,
            get_availability_for_date=get_avail,
            search_from=date(2024, 5, 10),
            search_days=7,
        )

        assert not result.has_solutions

    def test_respects_search_days_limit(self):
        """find_nearest() stops searching after search_days days."""
        call_count = {"n": 0}

        request = make_request([("5", 60, ["1"], 0)])

        def get_avail(d: date) -> dict[str, MasterAvailability]:
            call_count["n"] += 1
            return {}  # never available

        self.finder.find_nearest(
            request=request,
            get_availability_for_date=get_avail,
            search_from=date(2024, 5, 10),
            search_days=5,
        )

        assert call_count["n"] == 5


# ---------------------------------------------------------------------------
# BookingScorer
# ---------------------------------------------------------------------------


class TestBookingScorer:
    def _make_result(self, solutions: list) -> EngineResult:
        return EngineResult(solutions=solutions, mode=BookingMode.SINGLE_DAY)

    def _make_solution(
        self,
        starts_at: datetime,
        master_ids: list[str],
        durations: list[int],
        service_ids: list[str] | None = None,
    ) -> BookingChainSolution:
        from codex_tools.booking.dto import SingleServiceSolution

        items = [
            SingleServiceSolution(
                service_id=service_ids[i] if service_ids else f"svc_{i}",
                master_id=mid,
                start_time=starts_at,
                end_time=starts_at + timedelta(minutes=durations[i]),
                gap_end_time=starts_at + timedelta(minutes=durations[i]),
            )
            for i, mid in enumerate(master_ids)
        ]
        return BookingChainSolution(items=items)

    def test_preferred_master_gets_higher_score(self):
        """Solution with preferred master scores higher than one without."""
        scorer = BookingScorer(
            weights=ScoringWeights(preferred_master_bonus=10.0, same_master_bonus=0.0, min_idle_bonus_per_hour=0.0),
            preferred_master_ids=["3"],
        )

        sol_preferred = self._make_solution(dt(9), ["3"], [60])
        sol_other = self._make_solution(dt(9), ["5"], [60])

        result = scorer.score(self._make_result([sol_other, sol_preferred]))

        # Best (first after scoring) should be preferred master
        assert result.best.items[0].master_id == "3"

    def test_same_master_bonus_applied(self):
        """Two services with same master scores higher than with two masters."""
        scorer = BookingScorer(
            weights=ScoringWeights(preferred_master_bonus=0.0, same_master_bonus=5.0, min_idle_bonus_per_hour=0.0),
        )

        sol_same = self._make_solution(dt(9), ["1", "1"], [60, 60])
        sol_diff = self._make_solution(dt(9), ["1", "2"], [60, 60])

        result = scorer.score(self._make_result([sol_diff, sol_same]))

        assert result.solutions[0].items[0].master_id == result.solutions[0].items[1].master_id  # same master first

    def test_empty_result_returned_unchanged(self):
        """Scoring empty result returns it without error."""
        scorer = BookingScorer()
        empty = EngineResult(solutions=[], mode=BookingMode.SINGLE_DAY)
        result = scorer.score(empty)
        assert result.solutions == []

    def test_score_does_not_mutate_original(self):
        """score() returns new EngineResult, original unchanged."""
        scorer = BookingScorer(preferred_master_ids=["1"])
        sol = self._make_solution(dt(9), ["1"], [60])
        original = self._make_result([sol])
        original_score = original.solutions[0].score

        scored = scorer.score(original)

        # Original is frozen/unchanged
        assert original.solutions[0].score == original_score
        # Scored version has updated score
        assert scored.solutions[0].score > 0

    def test_best_scored_property(self):
        """EngineResult.best_scored returns solution with highest score."""
        sol_low = self._make_solution(dt(9), ["5"], [60])
        sol_high = self._make_solution(dt(10), ["3"], [60])

        # Manually set scores
        sol_low_scored = sol_low.model_copy(update={"score": 1.0})
        sol_high_scored = sol_high.model_copy(update={"score": 15.0})

        result = EngineResult(solutions=[sol_low_scored, sol_high_scored], mode=BookingMode.SINGLE_DAY)
        best = result.best_scored

        assert best is not None
        assert best.score == 15.0


# ---------------------------------------------------------------------------
# WaitlistEntry
# ---------------------------------------------------------------------------


class TestWaitlistEntry:
    def test_from_engine_result(self):
        """WaitlistEntry.from_engine_result() builds entry from result + date."""
        from codex_tools.booking.dto import SingleServiceSolution

        starts = datetime(2024, 5, 15, 10, 0)
        sol = BookingChainSolution(
            items=[
                SingleServiceSolution(
                    service_id="5",
                    master_id="1",
                    start_time=starts,
                    end_time=starts + timedelta(hours=1),
                    gap_end_time=starts + timedelta(hours=1),
                )
            ]
        )
        result = EngineResult(solutions=[sol], mode=BookingMode.SINGLE_DAY)
        entry = WaitlistEntry.from_engine_result(
            result=result,
            original_date=date(2024, 5, 10),
        )

        assert entry is not None
        assert entry.available_date == date(2024, 5, 15)
        assert entry.available_time == "10:00"
        assert entry.days_from_request == 5

    def test_from_engine_result_empty(self):
        """Returns None if result has no solutions."""
        empty = EngineResult(solutions=[], mode=BookingMode.SINGLE_DAY)
        entry = WaitlistEntry.from_engine_result(
            result=empty,
            original_date=date(2024, 5, 10),
        )
        assert entry is None
