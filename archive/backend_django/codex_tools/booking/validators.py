"""
codexn_tools.booking.validators
=================================
Validators for ensuring booking data correctness.

Used by ChainFinder to verify found solutions,
and can also be used independently in tests or the service layer.

Imports:
    from codexn_tools.booking import BookingValidator
"""

from datetime import datetime

from .dto import SingleServiceSolution


class BookingValidator:
    """
    A set of correctness checks for booking data.
    Unaffected by the ORM — operates exclusively on DTOs.

    Used by:
        - ChainFinder: Ensuring found chains have no conflicts.
        - Adapter: Final verification before creating Appointment instances in the DB.
        - Tests: Isolated logic verification without Django.

    Example:
        v = BookingValidator()

        # Check if a slot is free:
        ok = v.is_slot_free(
            slot_start=datetime(2024,5,10,10,0),
            slot_end=datetime(2024,5,10,11,0),
            busy_intervals=[(datetime(2024,5,10,9,0), datetime(2024,5,10,9,30))],
        )
        # → True (no overlap)

        # Check entire chain for conflicts:
        ok = v.no_conflicts(solutions)
    """

    def is_slot_free(
        self,
        slot_start: datetime,
        slot_end: datetime,
        busy_intervals: list[tuple[datetime, datetime]],
    ) -> bool:
        """
        Verifies that the slot [slot_start, slot_end) does not overlap
        with any of the busy intervals.

        Uses a "half-open" interval — [start, end). If slot_end == busy_start,
        it is NOT considered a conflict (adjacent slots are allowed).

        Args:
            slot_start: Start of the slot to check.
            slot_end: End of the slot to check.
            busy_intervals: List of busy intervals [(start, end), ...].

        Returns:
            True if the slot is free. False if there is an overlap.

        Example:
            # Busy 10:00-11:00. Requesting 10:30-11:30 → conflict:
            is_slot_free(10:30, 11:30, [(10:00, 11:00)]) → False

            # Requesting 11:00-12:00 → OK (adjacent slots):
            is_slot_free(11:00, 12:00, [(10:00, 11:00)]) → True
        """
        return all(not (slot_start < busy_end and slot_end > busy_start) for busy_start, busy_end in busy_intervals)

    def no_conflicts(
        self,
        solutions: list[SingleServiceSolution],
    ) -> bool:
        """
        Verifies that there are no master conflicts within a set of solutions.
        A professional cannot be occupied by two services simultaneously.

        Groups solutions by master_id and checks each group for overlaps.
        Used by ChainFinder after assembling the chain for final verification.

        Args:
            solutions: List of SingleServiceSolution objects (found slots).

        Returns:
            True if no conflicts exist. False if at least one professional is double-booked.

        Example:
            no_conflicts([
                SingleServiceSolution(master_id="1", start=9:00, gap_end=10:10),
                SingleServiceSolution(master_id="1", start=10:10, gap_end=11:10),
            ])
            # → True (slots are adjacent, no overlap)
        """
        # Group by master
        by_master: dict[str, list[SingleServiceSolution]] = {}
        for sol in solutions:
            by_master.setdefault(sol.master_id, []).append(sol)

        for _master_id, master_solutions in by_master.items():
            if len(master_solutions) < 2:
                continue
            # Sort by start time
            sorted_sols = sorted(master_solutions, key=lambda s: s.start_time)
            for i in range(len(sorted_sols) - 1):
                current = sorted_sols[i]
                next_sol = sorted_sols[i + 1]
                # gap_end_time includes the buffer — the next one must start after it
                if next_sol.start_time < current.gap_end_time:
                    return False

        return True

    def solution_fits_in_windows(
        self,
        solution: SingleServiceSolution,
        free_windows: list[tuple[datetime, datetime]],
    ) -> bool:
        """
        Verifies that a solution's slot [start_time, gap_end_time) fits entirely
        inside one of the professional's free windows.

        Used by ChainFinder to verify each found slot.

        Args:
            solution: Found slot for a single service.
            free_windows: Professional's free windows (from MasterAvailability).

        Returns:
            True if the slot fits perfectly inside one of the given free windows.
        """
        return any(solution.start_time >= w_start and solution.gap_end_time <= w_end for w_start, w_end in free_windows)
