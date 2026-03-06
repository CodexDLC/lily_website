"""
codex_tools.booking.scorer
============================
Evaluation and ranking of booking engine solutions.

Pure Python — no Django dependencies.
Applied AFTER ChainFinder.find() to sort solutions by quality.

Does not affect the search algorithm — only the output order.
BookingChainSolution.score is set here.

Quick start:
    from codex_tools.booking import ChainFinder
    from codex_tools.booking.scorer import BookingScorer, ScoringWeights

    result = ChainFinder().find(request, availability)

    scorer = BookingScorer(
        weights=ScoringWeights(preferred_master_bonus=15.0),
        preferred_master_ids=["3", "7"],
    )
    ranked = scorer.score(result)
    best = ranked.best  # solution with the highest score
"""

from dataclasses import dataclass

from .dto import BookingChainSolution, EngineResult


@dataclass
class ScoringWeights:
    """
    Weights for solution evaluation criteria. Configurable per project.

    All weights are additive: total score = sum of applicable bonuses.
    Higher score = more preferred solution.

    Fields:
        preferred_master_bonus (float):
            Bonus for each service with a preferred master.
            Passed via BookingScorer(preferred_master_ids=[...]).
            Example: client always visits Anya -> preferred_master_ids=["3"].

        same_master_bonus (float):
            Bonus if one master performs multiple services.
            Reduces the number of times the client must switch masters.

        min_idle_bonus_per_hour (float):
            Bonus for each hour of minimized idle time between services.
            Encourages compact chains.

        early_slot_penalty_per_hour (float):
            Penalty for each hour from the start of the workday to the first service.
            Encourages earlier slots (less index = better).
            Negative value is not needed here — subtracted automatically.

    Example (encourage early times AND preferred master):
        ScoringWeights(
            preferred_master_bonus=20.0,
            early_slot_penalty_per_hour=1.0,
        )
    """

    preferred_master_bonus: float = 10.0
    same_master_bonus: float = 5.0
    min_idle_bonus_per_hour: float = 2.0
    early_slot_penalty_per_hour: float = 0.0


class BookingScorer:
    """
    Evaluates engine solutions and returns an EngineResult with populated scores.

    Usage:
        scorer = BookingScorer(
            weights=ScoringWeights(preferred_master_bonus=15.0),
            preferred_master_ids=["3", "7"],
        )
        ranked = scorer.score(result)

        # Best solution by score (not just the earliest):
        print(ranked.best.score)
        print(ranked.best.to_display())

        # All solutions sorted by score (highest -> first):
        for solution in ranked.solutions:
            print(solution.score, solution.starts_at)

    Integration in a Django service:
        # In v2_booking_service.py, after ChainFinder.find():
        from features.booking.engine.scorer import BookingScorer

        scorer = BookingScorer(
            preferred_master_ids=[str(client.preferred_master_id)]
            if hasattr(client, 'preferred_master_id') and client.preferred_master_id
            else []
        )
        result = scorer.score(result)
        chain = self._pick_chain_by_start_time(result, selected_start_time)
    """

    def __init__(
        self,
        weights: ScoringWeights | None = None,
        preferred_master_ids: list[str] | None = None,
    ) -> None:
        """
        Args:
            weights: Criteria weights. None = ScoringWeights() with defaults.
            preferred_master_ids: List of IDs for preferred masters.
                                  Must be strings (str(master.pk)).
                                  On match -> preferred_master_bonus applied.
        """
        self.weights = weights or ScoringWeights()
        self.preferred_ids: set[str] = set(preferred_master_ids or [])

    def score(self, result: EngineResult) -> EngineResult:
        """
        Populates a score for each solution and returns a re-sorted EngineResult.

        Sorting: descending by score (best = first = result.best).
        Solutions with the same score are sorted by starts_at (earlier = better).

        Args:
            result: EngineResult from ChainFinder.find().

        Returns:
            New EngineResult (using frozen=True -> model_copy) with populated scores
            and solutions sorted by score DESC.
            If result is empty, it is returned unchanged.
        """
        if not result.solutions:
            return result

        scored = [self._score_solution(s) for s in result.solutions]
        # Sorting: score DESC, then starts_at ASC (earlier is better on equal score)
        scored.sort(key=lambda s: (-s.score, s.starts_at))

        return result.model_copy(update={"solutions": scored})

    def _score_solution(self, solution: BookingChainSolution) -> BookingChainSolution:
        """Calculates score for a single solution."""
        score = 0.0
        w = self.weights

        # --- Bonus for preferred master ---
        if self.preferred_ids:
            for item in solution.items:
                if item.master_id in self.preferred_ids:
                    score += w.preferred_master_bonus

        # --- Bonus for one master carrying out multiple services ---
        if w.same_master_bonus > 0 and len(solution.items) > 1:
            master_counts: dict[str, int] = {}
            for item in solution.items:
                master_counts[item.master_id] = master_counts.get(item.master_id, 0) + 1
            # Bonus for each pair of services with the same master
            for count in master_counts.values():
                if count > 1:
                    score += w.same_master_bonus * (count - 1)

        # --- Bonus for chain compactness (minimal idle time) ---
        if w.min_idle_bonus_per_hour > 0 and len(solution.items) > 1:
            # Idle time = span - total service duration
            total_service_minutes = sum(item.duration_minutes for item in solution.items)
            idle_minutes = solution.span_minutes - total_service_minutes
            idle_hours = idle_minutes / 60.0
            # Less idle = higher bonus (max for 0 idle)
            max_idle_hours = solution.span_minutes / 60.0
            compactness = 1.0 - (idle_hours / max_idle_hours) if max_idle_hours > 0 else 1.0
            score += w.min_idle_bonus_per_hour * compactness * max_idle_hours

        # --- Penalty for late start (encourages early slots) ---
        if w.early_slot_penalty_per_hour > 0:
            # Calculate hours from the start of the day (00:00) to starts_at
            starts_hour = solution.starts_at.hour + solution.starts_at.minute / 60.0
            score -= w.early_slot_penalty_per_hour * starts_hour

        return solution.model_copy(update={"score": round(score, 4)})
