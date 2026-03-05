"""
codexn_tools.booking.validators
=================================
Валидаторы корректности данных бронирования.

Используются ChainFinder-ом для проверки найденных решений,
а также могут применяться независимо в тестах или сервисном слое.

Импорт:
    from codexn_tools.booking import BookingValidator
"""

from datetime import datetime

from .dto import SingleServiceSolution


class BookingValidator:
    """
    Набор проверок корректности данных бронирования.
    Не знает об ORM — работает с DTO.

    Используется:
        - ChainFinder: проверка отсутствия конфликтов в найденных цепочках.
        - Адаптер: финальная проверка перед созданием Appointment в БД.
        - Тесты: изолированная проверка логики без Django.

    Пример:
        v = BookingValidator()

        # Проверить что слот свободен:
        ok = v.is_slot_free(
            slot_start=datetime(2024,5,10,10,0),
            slot_end=datetime(2024,5,10,11,0),
            busy_intervals=[(datetime(2024,5,10,9,0), datetime(2024,5,10,9,30))],
        )
        # → True (нет пересечения)

        # Проверить всю цепочку на конфликты:
        ok = v.no_conflicts(solutions)
    """

    def is_slot_free(
        self,
        slot_start: datetime,
        slot_end: datetime,
        busy_intervals: list[tuple[datetime, datetime]],
    ) -> bool:
        """
        Проверяет что слот [slot_start, slot_end) не пересекается
        ни с одним из занятых интервалов.

        Использует "открытый конец" — [start, end), то есть если slot_end == busy_start,
        это НЕ считается конфликтом (смежные слоты допустимы).

        Args:
            slot_start: Начало проверяемого слота.
            slot_end: Конец проверяемого слота.
            busy_intervals: Список занятых отрезков [(start, end), ...].

        Returns:
            True если слот свободен. False если есть пересечение.

        Пример:
            # Занято 10:00-11:00. Хотим 10:30-11:30 → конфликт:
            is_slot_free(10:30, 11:30, [(10:00, 11:00)]) → False

            # Хотим 11:00-12:00 → OK (смежные):
            is_slot_free(11:00, 12:00, [(10:00, 11:00)]) → True
        """
        return all(not (slot_start < busy_end and slot_end > busy_start) for busy_start, busy_end in busy_intervals)

    def no_conflicts(
        self,
        solutions: list[SingleServiceSolution],
    ) -> bool:
        """
        Проверяет что в наборе решений нет конфликтов по мастерам.
        Один мастер не может быть занят двумя услугами одновременно.

        Группирует решения по master_id и проверяет каждую группу на пересечения.
        Используется ChainFinder после сборки цепочки для финальной проверки.

        Args:
            solutions: Список SingleServiceSolution — найденных слотов.

        Returns:
            True если конфликтов нет. False если хотя бы один мастер занят дважды.

        Пример:
            no_conflicts([
                SingleServiceSolution(master_id="1", start=9:00, gap_end=10:10),
                SingleServiceSolution(master_id="1", start=10:10, gap_end=11:10),
            ])
            # → True (слоты смежные, нет пересечения)
        """
        # Группируем по мастерам
        by_master: dict[str, list[SingleServiceSolution]] = {}
        for sol in solutions:
            by_master.setdefault(sol.master_id, []).append(sol)

        for _master_id, master_solutions in by_master.items():
            if len(master_solutions) < 2:
                continue
            # Сортируем по времени начала
            sorted_sols = sorted(master_solutions, key=lambda s: s.start_time)
            for i in range(len(sorted_sols) - 1):
                current = sorted_sols[i]
                next_sol = sorted_sols[i + 1]
                # gap_end_time учитывает паузу — следующий должен начаться после неё
                if next_sol.start_time < current.gap_end_time:
                    return False

        return True

    def solution_fits_in_windows(
        self,
        solution: SingleServiceSolution,
        free_windows: list[tuple[datetime, datetime]],
    ) -> bool:
        """
        Проверяет что слот решения [start_time, gap_end_time) находится
        внутри одного из свободных окон мастера.

        Используется ChainFinder для верификации каждого найденного слота.

        Args:
            solution: Найденный слот для одной услуги.
            free_windows: Свободные окна мастера (из MasterAvailability).

        Returns:
            True если слот помещается в одно из окон.
        """
        return any(solution.start_time >= w_start and solution.gap_end_time <= w_end for w_start, w_end in free_windows)
