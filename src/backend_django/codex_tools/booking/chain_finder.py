"""
codexn_tools.booking.chain_finder
====================================
Главный алгоритм поиска цепочек слотов для N услуг.

Не зависит от Django/ORM -- работает только с DTO и datetime.
Является оркестратором для SlotCalculator и BookingValidator.

Принцип производительности:
    Внутри рекурсивного поиска (backtracking) используем лёгкий _SlotCandidate
    с __slots__ -- без Pydantic-валидации. Pydantic-объекты (SingleServiceSolution,
    BookingChainSolution) создаются ТОЛЬКО один раз для каждого найденного решения.
    Это критично при большом числе услуг и мастеров.

Импорт:
    from codexn_tools.booking import ChainFinder
"""

from collections.abc import Callable
from datetime import date, datetime, timedelta

from .dto import (
    BookingChainSolution,
    BookingEngineRequest,
    EngineResult,
    MasterAvailability,
    SingleServiceSolution,
)
from .modes import BookingMode
from .slot_calculator import SlotCalculator


class _SlotCandidate:
    """
    Лёгкое внутреннее представление назначенного слота внутри backtracking.

    Использует __slots__ для минимального потребления памяти и быстрого доступа.
    НЕ содержит Pydantic-валидации -- только сырые данные.

    Конвертируется в SingleServiceSolution (Pydantic) только для финального результата.
    """

    __slots__ = (
        "service_id",
        "master_id",
        "start_time",
        "end_time",
        "gap_end_time",
    )

    def __init__(
        self,
        service_id: str,
        master_id: str,
        start_time: datetime,
        end_time: datetime,
        gap_end_time: datetime,
    ) -> None:
        self.service_id = service_id
        self.master_id = master_id
        self.start_time = start_time
        self.end_time = end_time
        self.gap_end_time = gap_end_time

    def to_solution(self) -> SingleServiceSolution:
        """Конвертирует в Pydantic DTO для финального результата."""
        return SingleServiceSolution(
            service_id=self.service_id,
            master_id=self.master_id,
            start_time=self.start_time,
            end_time=self.end_time,
            gap_end_time=self.gap_end_time,
        )


class ChainFinder:
    """
    Находит комбинации временных слотов для N услуг (цепочки бронирования).

    Основной алгоритм: рекурсивный backtracking.
    Для каждой услуги перебирает возможных мастеров и их свободные окна.
    Проверяет отсутствие конфликтов с уже назначенными услугами в цепочке.

    Пример -- 1 услуга, любой свободный мастер:
        finder = ChainFinder(step_minutes=30)
        request = BookingEngineRequest(
            service_requests=[
                ServiceRequest(service_id="5", duration_minutes=60,
                               possible_master_ids=["1", "2"])
            ],
            booking_date=date(2024, 5, 10),
            mode=BookingMode.SINGLE_DAY,
        )
        result = finder.find(request, masters_availability)
        # result.solutions -- список BookingChainSolution
        # result.get_unique_start_times() -> ["09:00", "09:30", "10:00", ...]

    Пример -- 2 услуги в один день:
        request = BookingEngineRequest(
            service_requests=[svc_manicure, svc_pedicure],
            booking_date=date(2024, 5, 10),
            mode=BookingMode.SINGLE_DAY,
        )
        result = finder.find(request, availability)

    Пример -- запись к конкретному мастеру (MASTER_LOCKED):
        # Просто передай possible_master_ids=[locked_master_id]
        # и mode=BookingMode.MASTER_LOCKED

    Args:
        step_minutes: Шаг сетки слотов (по умолчанию 30 мин).
        min_start: Минимальное допустимое время начала первой услуги.
                   None = без ограничения (например, в тестах).
    """

    def __init__(
        self,
        step_minutes: int = 30,
        min_start: datetime | None = None,
    ) -> None:
        self.step_minutes = step_minutes
        self.min_start = min_start
        self._calc = SlotCalculator(step_minutes)

    def find(
        self,
        request: BookingEngineRequest,
        masters_availability: dict[str, MasterAvailability],
        max_solutions: int = 50,
        max_unique_starts: int | None = None,
    ) -> EngineResult:
        """
        Единая точка входа движка. Делегирует в нужный режим.

        Args:
            request: Входной запрос с услугами, датой и режимом.
            masters_availability: Словарь {master_id: MasterAvailability}.
                                  Подготавливается DjangoAvailabilityAdapter.
                                  Ключи -- строки (str(master.pk)).
            max_solutions: Максимальное количество вариантов которые движок
                           вернёт. Не влияет на корректность -- только на полноту.
            max_unique_starts: Остановиться после нахождения N уникальных
                               стартовых времён (по items[0].start_time).
                               None = без ограничения.
                               Пример: max_unique_starts=8 → только ближайшие 8 слотов,
                               даже если в дне их 16. Вдвое меньше итераций движка.

        Returns:
            EngineResult с найденными решениями.
            solutions отсортированы по времени начала первой услуги.
        """
        if request.mode in (BookingMode.SINGLE_DAY, BookingMode.MASTER_LOCKED):
            solutions = self._find_single_day(request, masters_availability, max_solutions, max_unique_starts)
        elif request.mode == BookingMode.MULTI_DAY:
            solutions = []  # TODO: реализовать MULTI_DAY
        else:
            solutions = []

        solutions.sort(key=lambda s: s.starts_at)
        return EngineResult(mode=request.mode, solutions=solutions)

    def find_nearest(
        self,
        request: BookingEngineRequest,
        get_availability_for_date: Callable[[date], dict[str, MasterAvailability]],
        search_from: date,
        search_days: int = 60,
        max_solutions_per_day: int = 1,
    ) -> EngineResult:
        """
        Ищет первый день с доступными слотами в диапазоне search_days.

        Используется для:
            - Перебронирования: мастер заболел → найти новую дату для N записей
            - Waitlist: ближайший свободный слот для уведомления клиента
            - MULTI_DAY планирования: найти первый день когда цепочка влезает

        Args:
            request: Запрос (booking_date будет заменён для каждого проверяемого дня).
            get_availability_for_date: callable(date) -> dict[str, MasterAvailability].
                                       Вызывается для каждого проверяемого дня.
                                       В Django-слое оборачивает DjangoAvailabilityAdapter.
            search_from: Дата с которой начинаем поиск (включительно).
            search_days: Сколько дней проверять максимум. По умолчанию 60.
            max_solutions_per_day: Сколько решений искать на каждый день.
                                   1 = быстрый режим (остановиться при первом).

        Returns:
            EngineResult первого дня с решениями.
            Если за search_days ничего не нашли — EngineResult(solutions=[]).

        Пример (Django-слой):
            adapter = DjangoAvailabilityAdapter()
            master_ids = [...]

            def get_avail(d):
                return adapter.build_masters_availability(master_ids, d)

            result = finder.find_nearest(request, get_avail, search_from=date.today())
            if result.has_solutions:
                print(result.best.starts_at)  # дата и время нового слота
        """
        for offset in range(search_days):
            check_date = search_from + timedelta(days=offset)

            # Обновляем дату в запросе (frozen=True → model_copy)
            day_request = request.model_copy(update={"booking_date": check_date})

            availability = get_availability_for_date(check_date)
            if not availability:
                continue

            result = self.find(day_request, availability, max_solutions=max_solutions_per_day)
            if result.has_solutions:
                return result

        return EngineResult(mode=request.mode, solutions=[])

    # ---------------------------------------------------------------------------
    # Режим SINGLE_DAY / MASTER_LOCKED
    # ---------------------------------------------------------------------------

    def _find_single_day(
        self,
        request: BookingEngineRequest,
        masters_availability: dict[str, MasterAvailability],
        max_solutions: int,
        max_unique_starts: int | None = None,
    ) -> list[BookingChainSolution]:
        """
        Поиск цепочки для режима 'все услуги в один день'.

        Производительность:
            Внутренне работает с _SlotCandidate (__slots__) -- без Pydantic.
            Pydantic-объекты создаются ТОЛЬКО для финальных решений.
            При 3 услугах x 3 мастерах x 20 слотов -- до 1800 итераций.

        Параметры request учитываемые в этом методе:
            request.overlap_allowed:
                True  → разные мастера работают независимо (могут параллельно).
                False → каждая следующая услуга начинается только после конца предыдущей.
            request.max_chain_duration_minutes:
                Если задан — отсекает ветви backtracking где цепочка уже превышает лимит.
        """
        solutions: list[BookingChainSolution] = []
        chain: list[_SlotCandidate] = []
        seen_starts: set[str] = set()  # уникальные времена начала первой услуги

        def backtrack(service_index: int) -> None:
            if len(solutions) >= max_solutions:
                return
            if max_unique_starts is not None and len(seen_starts) >= max_unique_starts:
                return

            if service_index >= len(request.service_requests):
                # Финальная проверка + конвертация в Pydantic только здесь
                if self._no_conflicts_fast(chain):
                    solution = BookingChainSolution(items=[c.to_solution() for c in chain])
                    solutions.append(solution)
                    seen_starts.add(chain[0].start_time.strftime("%H:%M"))
                return

            service_req = request.service_requests[service_index]
            duration_delta = timedelta(minutes=service_req.duration_minutes)
            gap_delta = timedelta(minutes=service_req.min_gap_after_minutes)

            for master_id in service_req.possible_master_ids:
                availability = masters_availability.get(master_id)
                if not availability:
                    continue

                # Занятые интервалы этого мастера в текущей цепочке
                master_busy = [(c.start_time, c.gap_end_time) for c in chain if c.master_id == master_id]

                effective_min = self._effective_min_start(master_busy, availability.buffer_between_minutes)

                # overlap_allowed=False: каждая услуга начинается после конца всех предыдущих
                if not request.overlap_allowed and chain:
                    chain_ends_at = max(c.end_time for c in chain)
                    if effective_min is None or effective_min < chain_ends_at:
                        effective_min = chain_ends_at

                for window_start, window_end in availability.free_windows:
                    slots = self._calc.find_slots_in_window(
                        window_start=window_start,
                        window_end=window_end,
                        duration_minutes=service_req.duration_minutes,
                        min_start=effective_min,
                    )

                    for slot_start in slots:
                        if len(solutions) >= max_solutions:
                            return
                        if max_unique_starts is not None and len(seen_starts) >= max_unique_starts:
                            return

                        slot_end = slot_start + duration_delta
                        gap_end = slot_end + gap_delta

                        # Простое сравнение datetime -- без Pydantic
                        if not self._is_slot_free_fast(slot_start, gap_end, master_busy):
                            continue

                        # Проверка максимальной длительности цепочки
                        if request.max_chain_duration_minutes is not None and chain:
                            chain_start = min(c.start_time for c in chain)
                            prospective_span = int(
                                (max(slot_end, max(c.end_time for c in chain)) - chain_start).total_seconds() / 60
                            )
                            if prospective_span > request.max_chain_duration_minutes:
                                continue  # отсекаем ветвь — цепочка слишком длинная

                        chain.append(
                            _SlotCandidate(
                                service_id=service_req.service_id,
                                master_id=master_id,
                                start_time=slot_start,
                                end_time=slot_end,
                                gap_end_time=gap_end,
                            )
                        )
                        backtrack(service_index + 1)
                        chain.pop()

        backtrack(0)
        return solutions

    # ---------------------------------------------------------------------------
    # Быстрые внутренние проверки (без Pydantic -- только stdlib)
    # ---------------------------------------------------------------------------

    @staticmethod
    def _is_slot_free_fast(
        slot_start: datetime,
        slot_end: datetime,
        busy_intervals: list[tuple[datetime, datetime]],
    ) -> bool:
        """Быстрая проверка свободности слота. Без Pydantic."""
        return all(not (slot_start < b_end and slot_end > b_start) for b_start, b_end in busy_intervals)

    @staticmethod
    def _no_conflicts_fast(chain: list["_SlotCandidate"]) -> bool:
        """Финальная проверка цепочки на конфликты по мастерам. Без Pydantic."""
        by_master: dict[str, list[_SlotCandidate]] = {}
        for c in chain:
            if c.master_id not in by_master:
                by_master[c.master_id] = []
            by_master[c.master_id].append(c)

        for slots in by_master.values():
            if len(slots) < 2:
                continue
            sorted_slots = sorted(slots, key=lambda s: s.start_time)
            for i in range(len(sorted_slots) - 1):
                if sorted_slots[i + 1].start_time < sorted_slots[i].gap_end_time:
                    return False

        return True

    def _effective_min_start(
        self,
        master_busy: list[tuple[datetime, datetime]],
        buffer_minutes: int,
    ) -> datetime | None:
        """
        Минимально допустимое время старта для мастера.

        Учитывает:
            - self.min_start (глобальный -- "не раньше чем через N мин от сейчас")
            - Конец последнего занятого слота + буфер между клиентами
        """
        candidates: list[datetime] = []

        if self.min_start:
            candidates.append(self.min_start)

        if master_busy:
            last_end = max(end for _, end in master_busy)
            candidates.append(last_end + timedelta(minutes=buffer_minutes))

        return max(candidates) if candidates else None
