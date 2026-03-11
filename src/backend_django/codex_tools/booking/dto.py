"""
codexn_tools.booking.dto
=========================
Pydantic v2 DTO (Data Transfer Objects) for the booking engine.

All models are immutable (frozen=True) — the engine does not mutate inputs.
No Django imports. Only Python stdlib + pydantic.

Imports:
    from codexn_tools.booking import (
        BookingEngineRequest, ServiceRequest,
        MasterAvailability, EngineResult, BookingChainSolution,
    )
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .modes import BookingMode

# ---------------------------------------------------------------------------
# Входные DTO (что подаётся в движок)
# ---------------------------------------------------------------------------


class ServiceRequest(BaseModel, frozen=True):
    """
    Request for a single service within a booking.

    The engine does not know about specific professionals — only about those
    who *are capable* of performing the service (possible_master_ids).
    Selecting a specific professional is the job of ChainFinder.

    Fields:
        service_id (str):
            Unique identifier of the service. String for universality
            (can be "5", "uuid-xxx", "manicure" — doesn't matter).

        duration_minutes (int):
            Duration of the service in minutes. Must be > 0.

        min_gap_after_minutes (int):
            Minimum gap (minutes) after this service before the next one
            in the chain. Default is 0 (no gap).
            Example: after coloring, 30 mins waiting is needed → min_gap_after_minutes=30

        possible_master_ids (list[str]):
            List of master ids capable of performing this service.
            The engine chooses an available master from this list.
            For MASTER_LOCKED, contains exactly one element.

        parallel_group (str | None):
            Tag for parallel execution group.
            Services with the same parallel_group can be performed simultaneously
            by different masters (overlap_allowed=True must be set in the request).
            None = service is performed independently (standard behavior).

            Example — pedicure and manicure in parallel:
                svc_mani = ServiceRequest(..., parallel_group="session_1")
                svc_pedi = ServiceRequest(..., parallel_group="session_1")
                # Both services can start at the same time with different masters.

            Example — consultation → procedures in parallel:
                svc_consult = ServiceRequest(..., parallel_group=None)   # first
                svc_a = ServiceRequest(..., parallel_group="procedures") # then in parallel
                svc_b = ServiceRequest(..., parallel_group="procedures") # then in parallel

    Example:
        ServiceRequest(
            service_id="5",
            duration_minutes=60,
            possible_master_ids=["1", "3", "7"],
        )

    Example with parallel group:
        ServiceRequest(
            service_id="mani",
            duration_minutes=60,
            possible_master_ids=["1", "2"],
            parallel_group="together",
        )
    """

    service_id: str
    duration_minutes: int = Field(gt=0, description="Длительность в минутах")
    min_gap_after_minutes: int = Field(default=0, ge=0, description="Пауза после услуги перед следующей")
    possible_master_ids: list[str] = Field(min_length=1, description="Хотя бы один мастер должен быть указан")
    parallel_group: str | None = Field(
        default=None,
        description="Метка группы параллельного выполнения (одинаковый тег = одновременно)",
    )

    @property
    def total_block_minutes(self) -> int:
        """Total time that blocks the master: duration + gap after."""
        return self.duration_minutes + self.min_gap_after_minutes

    def __repr__(self) -> str:
        return f"<ServiceRequest id={self.service_id} dur={self.duration_minutes}>"


class BookingEngineRequest(BaseModel, frozen=True):
    """
    Input request to the engine. Describes WHAT needs to be booked.

    Fields:
        service_requests (list[ServiceRequest]):
            List of services to book. Order is important for SINGLE_DAY —
            the engine will schedule them in the specified order.
            Minimum 1 service.

        booking_date (date):
            Booking date. Used for SINGLE_DAY and MASTER_LOCKED.
            For MULTI_DAY — date of the first service (others — separately, future).

        mode (BookingMode):
            Engine operating mode. Default is SINGLE_DAY.

        overlap_allowed (bool):
            Allow parallel execution of services by different masters.
            False (default) — each subsequent service starts only after the end
            of the previous one (strictly sequential, useful for pipelines
            where a client moves from master to master).
            True — masters work independently, services can
            start simultaneously (pedicure + lashes at the same time).

        group_size (int):
            DEPRECATED. Use duplication of ServiceRequest with parallel_group.
            Number of clients in a group. Default is 1.

        max_chain_duration_minutes (int | None):
            Maximum total duration of the entire booking in minutes
            (from the start of the first to the end of the last service).
            None = no limit.
            Example: max_chain_duration_minutes=240 → booking no longer than 4 hours.

        days_gap (list[int] | None):
            For MULTI_DAY: offset in days for each service from booking_date.
            [0, 0, 7] → first two services on booking_date, third after 7 days.
            None = all services on one day (SINGLE_DAY behavior).
            IMPORTANT: used only in MULTI_DAY mode (not implemented yet).

    Example:
        BookingEngineRequest(
            service_requests=[svc_manicure, svc_pedicure],
            booking_date=date(2024, 5, 10),
            mode=BookingMode.SINGLE_DAY,
        )

    Example with parallel services:
        BookingEngineRequest(
            service_requests=[svc_manicure, svc_pedicure],
            booking_date=date(2024, 5, 10),
            overlap_allowed=True,   # manicure and pedicure simultaneously
        )

    Example with duration limit:
        BookingEngineRequest(
            service_requests=[svc_a, svc_b, svc_c],
            booking_date=date(2024, 5, 10),
            max_chain_duration_minutes=180,  # not more than 3 hours
        )
    """

    service_requests: list[ServiceRequest] = Field(default_factory=list, description="Список запрашиваемых услуг")
    booking_date: date
    mode: BookingMode = BookingMode.SINGLE_DAY
    overlap_allowed: bool = Field(
        default=False,
        description="Разрешить параллельное выполнение услуг разными мастерами",
    )
    group_size: int = Field(
        default=1,
        ge=1,
        description="DEPRECATED. Используйте дублирование ServiceRequest с parallel_group.",
    )
    max_chain_duration_minutes: int | None = Field(
        default=None,
        ge=1,
        description="Макс. длительность всей цепочки в минутах (None = без лимита)",
    )
    days_gap: list[int] | None = Field(
        default=None,
        description="Смещение в днях для каждой услуги (только MULTI_DAY)",
    )

    @property
    def total_duration_minutes(self) -> int:
        """Total duration of all services (without gap pauses)."""
        return sum(s.duration_minutes for s in self.service_requests)

    @property
    def total_block_minutes(self) -> int:
        """
        Total blocking time including pauses between services.
        Used for quick check: does the chain fit into the window.
        """
        return sum(s.total_block_minutes for s in self.service_requests)

    def __repr__(self) -> str:
        return f"<BookingEngineRequest date={self.booking_date} services={len(self.service_requests)}>"


# ---------------------------------------------------------------------------
# Данные доступности (подготавливаются адаптером)
# ---------------------------------------------------------------------------


class MasterAvailability(BaseModel, frozen=True):
    """
    Free time windows of a master for a given date.
    Prepared by the adapter (DjangoAvailabilityAdapter),
    the engine only reads them — does not query the DB.

    Fields:
        master_id (str):
            Master identifier (string for universality).

        free_windows (list[tuple[datetime, datetime]]):
            List of free windows in format [(window_start, window_end), ...].
            Windows are already cleared of busy slots and breaks.
            Sorted by start time.

        buffer_between_minutes (int):
            Buffer between clients for this master.
            Taken into account when finding the next slot.

    Example:
        MasterAvailability(
            master_id="3",
            free_windows=[
                (datetime(2024,5,10,9,0), datetime(2024,5,10,12,0)),
                (datetime(2024,5,10,13,0), datetime(2024,5,10,18,0)),
            ],
            buffer_between_minutes=10,
        )
    """

    master_id: str
    free_windows: list[tuple[datetime, datetime]] = Field(default_factory=list)
    buffer_between_minutes: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_windows_order(self) -> "MasterAvailability":
        """Checks that each window: start < end."""
        for start, end in self.free_windows:
            if start >= end:
                raise ValueError(f"Мастер {self.master_id}: start={start} >= end={end}")
        return self

    def __repr__(self) -> str:
        return f"<MasterAvailability master={self.master_id} windows={len(self.free_windows)}>"


# ---------------------------------------------------------------------------
# Выходные DTO (результат работы движка)
# ---------------------------------------------------------------------------


class SingleServiceSolution(BaseModel, frozen=True):
    """
    Found slot for a single service in a chain.

    Fields:
        service_id (str): Id of the service from ServiceRequest.
        master_id (str): Id of the selected master.
        start_time (datetime): Start time of the service execution.
        end_time (datetime): End time of the service execution (without gap).
        gap_end_time (datetime): End time including pause (master is busy until this moment).
    """

    service_id: str
    master_id: str
    start_time: datetime
    end_time: datetime
    gap_end_time: datetime  # end_time + min_gap_after_minutes

    @property
    def duration_minutes(self) -> int:
        """Actual duration of the service in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def __repr__(self) -> str:
        # GDPR Safe: Only IDs and Times. No notes, names, or PII.
        return (
            f"<SingleServiceSolution svc={self.service_id} "
            f"mst={self.master_id} "
            f"start={self.start_time.strftime('%H:%M')}>"
        )


class BookingChainSolution(BaseModel, frozen=True):
    """
    One complete solution for the entire request (set of slots for all services).
    Found by the engine. Guarantees no conflicts between services.

    Fields:
        items (list[SingleServiceSolution]):
            List of slots in the order of service execution.

        score (float):
            Quality score of the solution. Default 0.0.
            Higher score = more preferred solution.
            Usage example:
                - preferred master → score += 10
                - minimal idle time between services → score += 2 for every hour
                - one master for multiple services → score += 5
            Used during sorting and selecting result.best.
            Can be set via ChainFinder or an external scorer.

    Properties:
        starts_at: start time of the first service
        ends_at:   end time of the last service
        span_minutes: total time from the start of the first to the end of the last service
    """

    items: list[SingleServiceSolution] = Field(min_length=1)
    score: float = Field(default=0.0, description="Оценка качества решения")

    @property
    def starts_at(self) -> datetime:
        """Start of the first service in the chain."""
        return min(s.start_time for s in self.items)

    @property
    def ends_at(self) -> datetime:
        """End of the last service (without gap)."""
        return max(s.end_time for s in self.items)

    @property
    def span_minutes(self) -> int:
        """Total time from the start of the first to the end of the last service."""
        return int((self.ends_at - self.starts_at).total_seconds() / 60)

    def to_display(self) -> dict[str, Any]:
        """
        Converts the solution into a dict for UI/serialization.
        Returns: {service_id: {master_id, start, end}, ...}
        """
        return {
            item.service_id: {
                "master_id": item.master_id,
                "start": item.start_time.strftime("%H:%M"),
                "end": item.end_time.strftime("%H:%M"),
            }
            for item in self.items
        }

    def __repr__(self) -> str:
        # GDPR Safe: Only structural info.
        return f"<BookingChainSolution score={self.score:.2f} items={self.items}>"


class EngineResult(BaseModel, frozen=True):
    """
    Engine work result. Returned by ChainFinder.find().

    Fields:
        mode (BookingMode): Mode in which the search was performed.
        solutions (list[BookingChainSolution]):
            Found schedule options. Empty list = found nothing.
            After BookingScorer.score() — sorted by score DESC.
            By default (without scorer) — by start time of the first service.

    Properties:
        has_solutions (bool): Quick check for results availability.
        best (BookingChainSolution | None): First option (earliest or best by score).
        best_scored (BookingChainSolution | None): Option with the maximum score.

    Example usage without scorer (first by time):
        result = ChainFinder().find(request, availability)
        if result.has_solutions:
            print(result.best.starts_at)

    Example with BookingScorer (first by quality):
        result = BookingScorer(preferred_master_ids=["3"]).score(result)
        print(result.best.score)        # highest score
        print(result.best_scored.score) # same thing
    """

    mode: BookingMode
    solutions: list[BookingChainSolution] = Field(default_factory=list)

    @property
    def has_solutions(self) -> bool:
        """True if the engine found at least one solution."""
        return len(self.solutions) > 0

    @property
    def best(self) -> BookingChainSolution | None:
        """
        The first option in the list of solutions.
        - Without scorer: earliest by start time.
        - After BookingScorer.score(): with the highest score.
        None if there are no solutions.
        """
        return self.solutions[0] if self.solutions else None

    @property
    def best_scored(self) -> BookingChainSolution | None:
        """
        Option with the maximum score among all solutions.

        Differs from best if scorer has not been applied yet —
        in this case best = earliest, best_scored = highest_score.
        After BookingScorer.score() they match (list is already sorted).

        None if there are no solutions.
        """
        if not self.solutions:
            return None
        return max(self.solutions, key=lambda s: s.score)

    def get_unique_start_times(self) -> list[str]:
        """
        Returns a list of unique start times of the first service.
        Used to display a grid of slots in the UI.
        Format: ["09:00", "09:30", "10:00", ...]
        """
        times = {s.starts_at.strftime("%H:%M") for s in self.solutions}
        return sorted(times)

    def __repr__(self) -> str:
        return f"<EngineResult mode={self.mode} solutions_count={len(self.solutions)}>"


# ---------------------------------------------------------------------------
# Waitlist DTO (результат find_nearest / waitlist-уведомлений)
# ---------------------------------------------------------------------------


class WaitlistEntry(BaseModel, frozen=True):
    """
    Nearest available slot to notify a client from the waitlist.

    Returned by ChainFinder.find_nearest() via an auxiliary service
    or by a waitlist-worker when a slot becomes available.

    Fields:
        available_date (date): Date when the slot became available.
        available_time (str): Start time of the first service ("HH:MM").
        solution (BookingChainSolution): Complete found solution.
        days_from_request (int): How many days from the original request date.

    Example usage:
        # In the waitlist-worker, when an appointment is canceled:
        result = finder.find_nearest(request, get_avail, search_from=original_date)
        if result.has_solutions:
            entry = WaitlistEntry.from_engine_result(result, original_date)
            notify_client(entry)  # send email/telegram

    Example creation:
        entry = WaitlistEntry(
            available_date=date(2024, 5, 15),
            available_time="10:30",
            solution=result.best,
            days_from_request=5,
        )
    """

    available_date: date
    available_time: str  # "HH:MM"
    solution: BookingChainSolution
    days_from_request: int = 0

    @classmethod
    def from_engine_result(
        cls,
        result: "EngineResult",
        original_date: date,
    ) -> "WaitlistEntry | None":
        """
        Creates WaitlistEntry from EngineResult of a successful find_nearest().

        Args:
            result: EngineResult with at least one solution.
            original_date: Original request date (for calculating days_from_request).

        Returns:
            WaitlistEntry or None if result is empty.
        """
        if not result.has_solutions:
            return None

        solution = result.best
        if solution is None:
            return None

        available_date = solution.starts_at.date()
        available_time = solution.starts_at.strftime("%H:%M")
        days_delta = (available_date - original_date).days

        return cls(
            available_date=available_date,
            available_time=available_time,
            solution=solution,
            days_from_request=max(0, days_delta),
        )

    def __repr__(self) -> str:
        return f"<WaitlistEntry date={self.available_date} time={self.available_time}>"
