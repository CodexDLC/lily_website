"""
codexn_tools.booking.scorer
============================
Оценка и ранжирование решений движка бронирования.

Чистый Python — никаких Django-зависимостей.
Применяется ПОСЛЕ ChainFinder.find() для сортировки решений по качеству.

Не влияет на алгоритм поиска — только на порядок вывода.
BookingChainSolution.score устанавливается здесь.

Быстрый старт:
    from codexn_tools.booking import ChainFinder
    from codexn_tools.booking.scorer import BookingScorer, ScoringWeights

    result = ChainFinder().find(request, availability)

    scorer = BookingScorer(
        weights=ScoringWeights(preferred_master_bonus=15.0),
        preferred_master_ids=["3", "7"],
    )
    ranked = scorer.score(result)
    best = ranked.best  # решение с наивысшим score
"""

from dataclasses import dataclass

from .dto import BookingChainSolution, EngineResult


@dataclass
class ScoringWeights:
    """
    Веса критериев оценки решения. Настраиваются под конкретный проект.

    Все веса аддитивны: итоговый score = сумма применимых бонусов.
    Более высокий score = более предпочтительное решение.

    Поля:
        preferred_master_bonus (float):
            Бонус за каждую услугу у предпочтительного мастера.
            Передаётся через BookingScorer(preferred_master_ids=[...]).
            Пример: клиент всегда ходит к Ане → preferred_master_ids=["3"].

        same_master_bonus (float):
            Бонус если один мастер выполняет несколько услуг.
            Уменьшает число пересадок клиента.

        min_idle_bonus_per_hour (float):
            Бонус за каждый час минимального простоя между услугами.
            Поощряет компактные цепочки.

        early_slot_penalty_per_hour (float):
            Штраф за каждый час от начала рабочего дня до первой услуги.
            Поощряет ранние слоты (меньше = лучше).
            Отрицательное значение здесь не нужно — вычитается автоматически.

    Пример (поощрять раннее время И предпочтительного мастера):
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
    Оценивает решения движка и возвращает EngineResult с проставленными score.

    Использование:
        scorer = BookingScorer(
            weights=ScoringWeights(preferred_master_bonus=15.0),
            preferred_master_ids=["3", "7"],
        )
        ranked = scorer.score(result)

        # Лучшее решение по score (не просто самое раннее):
        print(ranked.best.score)
        print(ranked.best.to_display())

        # Все решения отсортированы по score (высокий → первый):
        for solution in ranked.solutions:
            print(solution.score, solution.starts_at)

    Интеграция в Django-сервис:
        # В v2_booking_service.py, после ChainFinder.find():
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
            weights: Веса критериев. None = ScoringWeights() с дефолтами.
            preferred_master_ids: Список id предпочтительных мастеров.
                                  Строки (str(master.pk)).
                                  При совпадении → preferred_master_bonus.
        """
        self.weights = weights or ScoringWeights()
        self.preferred_ids: set[str] = set(preferred_master_ids or [])

    def score(self, result: EngineResult) -> EngineResult:
        """
        Проставляет score каждому решению и возвращает пересортированный EngineResult.

        Сортировка: по убыванию score (лучшее = первое = result.best).
        Решения с одинаковым score сортируются по starts_at (раньше = лучше).

        Args:
            result: EngineResult от ChainFinder.find().

        Returns:
            Новый EngineResult (frozen=True → model_copy) с проставленными score
            и решениями отсортированными по score DESC.
            Пустой result возвращается без изменений.
        """
        if not result.solutions:
            return result

        scored = [self._score_solution(s) for s in result.solutions]
        # Сортировка: score DESC, затем starts_at ASC (раньше лучше при равном score)
        scored.sort(key=lambda s: (-s.score, s.starts_at))

        return result.model_copy(update={"solutions": scored})

    def _score_solution(self, solution: BookingChainSolution) -> BookingChainSolution:
        """Рассчитывает score для одного решения."""
        score = 0.0
        w = self.weights

        # --- Бонус за предпочтительного мастера ---
        if self.preferred_ids:
            for item in solution.items:
                if item.master_id in self.preferred_ids:
                    score += w.preferred_master_bonus

        # --- Бонус за одного мастера на несколько услуг ---
        if w.same_master_bonus > 0 and len(solution.items) > 1:
            master_counts: dict[str, int] = {}
            for item in solution.items:
                master_counts[item.master_id] = master_counts.get(item.master_id, 0) + 1
            # Бонус за каждую пару услуг у одного мастера
            for count in master_counts.values():
                if count > 1:
                    score += w.same_master_bonus * (count - 1)

        # --- Бонус за компактность цепочки (минимальный простой) ---
        if w.min_idle_bonus_per_hour > 0 and len(solution.items) > 1:
            # Простой = span - суммарная длительность услуг
            total_service_minutes = sum(item.duration_minutes for item in solution.items)
            idle_minutes = solution.span_minutes - total_service_minutes
            idle_hours = idle_minutes / 60.0
            # Меньше простоя = выше бонус (максимум за 0 простоя)
            max_idle_hours = solution.span_minutes / 60.0
            compactness = 1.0 - (idle_hours / max_idle_hours) if max_idle_hours > 0 else 1.0
            score += w.min_idle_bonus_per_hour * compactness * max_idle_hours

        # --- Штраф за позднее начало (поощрение ранних слотов) ---
        if w.early_slot_penalty_per_hour > 0:
            # Считаем часы от начала дня (00:00) до starts_at
            starts_hour = solution.starts_at.hour + solution.starts_at.minute / 60.0
            score -= w.early_slot_penalty_per_hour * starts_hour

        return solution.model_copy(update={"score": round(score, 4)})
