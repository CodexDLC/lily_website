"""
codexn_tools.booking.slot_calculator
======================================
Базовые операции со слотами внутри временных окон.

Это "математика без ORM" — работает с datetime объектами, не знает о Django.
Используется внутри ChainFinder, а также может применяться независимо.

Импорт:
    from codexn_tools.booking import SlotCalculator
"""

from datetime import datetime, timedelta


class SlotCalculator:
    """
    Генератор слотов внутри свободного временного окна (sliding window).

    Не зависит от ORM. Работает с datetime-объектами.
    Ядро алгоритма — переработанная логика из SlotService V1,
    вынесенная из Django-контекста.

    Пример использования:
        calc = SlotCalculator(step_minutes=30)

        # Получить все возможные слоты в окне с 9:00 до 12:00 для услуги 60 мин:
        slots = calc.find_slots_in_window(
            window_start=datetime(2024, 5, 10, 9, 0),
            window_end=datetime(2024, 5, 10, 12, 0),
            duration_minutes=60,
        )
        # → [datetime(2024,5,10,9,0), datetime(2024,5,10,9,30), datetime(2024,5,10,10,0), ...]

        # Получить свободные окна из рабочего дня:
        windows = calc.merge_free_windows(
            work_start=datetime(2024,5,10,9,0),
            work_end=datetime(2024,5,10,18,0),
            busy_intervals=[(datetime(2024,5,10,10,0), datetime(2024,5,10,11,0))],
        )
        # → [(9:00, 10:00), (11:00, 18:00)]
    """

    def __init__(self, step_minutes: int = 30) -> None:
        """
        Args:
            step_minutes: Шаг сетки слотов в минутах. По умолчанию 30.
                          Определяет с каким интервалом предлагаются слоты.
        """
        if step_minutes <= 0:
            raise ValueError(f"step_minutes должен быть > 0, получен: {step_minutes}")
        self.step_minutes = step_minutes
        self._step_delta = timedelta(minutes=step_minutes)

    def find_slots_in_window(
        self,
        window_start: datetime,
        window_end: datetime,
        duration_minutes: int,
        min_start: datetime | None = None,
    ) -> list[datetime]:
        """
        Возвращает список возможных стартовых времён внутри окна.

        Алгоритм: скользящее окно (sliding window) с шагом self.step_minutes.
        Каждый кандидат проверяется: помещается ли услуга [slot, slot+duration]
        до конца окна.

        Args:
            window_start: Начало свободного временного окна.
            window_end: Конец свободного временного окна.
            duration_minutes: Длительность услуги в минутах.
            min_start: Минимально допустимое время начала (например, "не ранее чем
                       через 15 минут от текущего времени"). None = без ограничения.

        Returns:
            Список datetime — возможные моменты начала услуги.
            Пустой список если услуга не влезает в окно.

        Пример:
            # Окно 9:00-11:00, услуга 60 мин, шаг 30 мин:
            # → [9:00, 9:30, 10:00]  (10:30 + 60 мин = 11:30, не влезает)
        """
        duration_delta = timedelta(minutes=duration_minutes)

        # Быстрая проверка: окно в принципе достаточно для услуги
        if window_end - window_start < duration_delta:
            return []

        slots: list[datetime] = []
        current = window_start

        # Если есть min_start — двигаем указатель к ближайшему шагу сетки
        if min_start and current < min_start:
            current = self._align_to_grid(min_start, window_start)

        while current + duration_delta <= window_end:
            slots.append(current)
            current += self._step_delta

        return slots

    def merge_free_windows(
        self,
        work_start: datetime,
        work_end: datetime,
        busy_intervals: list[tuple[datetime, datetime]],
        break_interval: tuple[datetime, datetime] | None = None,
        buffer_minutes: int = 0,
    ) -> list[tuple[datetime, datetime]]:
        """
        Вычисляет список свободных окон из рабочего дня.

        Из промежутка [work_start, work_end] вычитает:
        - busy_intervals (занятые записи)
        - break_interval (обед/перерыв мастера)
        - buffer_minutes (буфер после каждого занятого интервала)

        Args:
            work_start: Начало рабочего дня мастера.
            work_end: Конец рабочего дня мастера.
            busy_intervals: Список занятых отрезков [(start, end), ...].
                            Должны быть в пределах [work_start, work_end].
                            Не требуют предварительной сортировки.
            break_interval: Перерыв мастера (обед), tuple (start, end) или None.
            buffer_minutes: Буфер в минутах добавляемый после каждой занятой записи.
                            Даёт мастеру время на подготовку к следующему клиенту.

        Returns:
            Список свободных окон [(start, end), ...] отсортированных по времени.
            Окна с нулевой длиной не включаются.

        Пример:
            # Рабочий день 9:00-18:00, запись 10:00-11:00, обед 13:00-14:00
            windows = calc.merge_free_windows(
                work_start=dt(9,0), work_end=dt(18,0),
                busy_intervals=[(dt(10,0), dt(11,0))],
                break_interval=(dt(13,0), dt(14,0)),
                buffer_minutes=10,
            )
            # → [(9:00, 10:00), (11:10, 13:00), (14:00, 18:00)]
        """
        buffer_delta = timedelta(minutes=buffer_minutes)

        # Собираем все "занятые" интервалы: записи + перерыв
        blocked: list[tuple[datetime, datetime]] = []
        for b_start, b_end in busy_intervals:
            # Применяем буфер после занятой записи
            blocked.append((b_start, b_end + buffer_delta))

        if break_interval:
            blocked.append(break_interval)

        # Сортируем и мёрджим пересекающиеся интервалы
        blocked = self._merge_intervals(blocked)

        # Вычисляем свободные окна
        free_windows: list[tuple[datetime, datetime]] = []
        current_ptr = work_start

        for b_start, b_end in blocked:
            # Отсекаем выход за рамки рабочего дня
            b_start = max(b_start, work_start)
            b_end = min(b_end, work_end)

            if b_start > current_ptr:
                free_windows.append((current_ptr, b_start))

            current_ptr = max(current_ptr, b_end)

        # Остаток после последнего занятого блока
        if current_ptr < work_end:
            free_windows.append((current_ptr, work_end))

        return free_windows

    def find_gaps(
        self,
        free_windows: list[tuple[datetime, datetime]],
        min_gap_minutes: int,
    ) -> list[tuple[datetime, datetime, int]]:
        """
        Находит все свободные окна минимальной длины в расписании мастера.

        Используется для:
            - "Забить день мастера": найти свободные промежутки куда можно
              поставить дополнительные записи (акция, последний слот перед уходом)
            - Анализа загрузки: сколько свободного времени у мастера
            - Уведомлений: мастер освободился на N минут → предложить клиенту

        Args:
            free_windows: Свободные окна из MasterAvailability.free_windows
                          (уже очищены от занятых записей).
            min_gap_minutes: Минимальная длина окна в минутах.
                             Окна короче этого значения не возвращаются.

        Returns:
            Список (window_start, window_end, duration_minutes) — окна
            длиннее min_gap_minutes, отсортированные по времени начала.

        Пример:
            # Мастер свободен: 9:00-10:00, 11:30-14:00, 16:00-18:00
            # Ищем окна >= 60 минут:
            gaps = calc.find_gaps(free_windows, min_gap_minutes=60)
            # → [(9:00, 10:00, 60), (11:30, 14:00, 150), (16:00, 18:00, 120)]

            # Ищем окна >= 90 минут:
            gaps = calc.find_gaps(free_windows, min_gap_minutes=90)
            # → [(11:30, 14:00, 150), (16:00, 18:00, 120)]
        """
        result: list[tuple[datetime, datetime, int]] = []

        for w_start, w_end in free_windows:
            duration = int((w_end - w_start).total_seconds() / 60)
            if duration >= min_gap_minutes:
                result.append((w_start, w_end, duration))

        result.sort(key=lambda x: x[0])
        return result

    def split_window_by_service(
        self,
        window_start: datetime,
        window_end: datetime,
        service_start: datetime,
        service_end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """
        Разбивает свободное окно на части вокруг занятого отрезка услуги.

        Используется при динамическом расчёте: "если поставить услугу сюда —
        какие окна останутся свободными для следующих?"

        Args:
            window_start: Начало свободного окна.
            window_end: Конец свободного окна.
            service_start: Начало занятого отрезка (должен быть внутри окна).
            service_end: Конец занятого отрезка (должен быть внутри окна).

        Returns:
            Список оставшихся свободных окон (0, 1 или 2 элемента).

        Пример:
            # Окно 9:00-18:00, услуга 11:00-12:00:
            split_window_by_service(9:00, 18:00, 11:00, 12:00)
            # → [(9:00, 11:00), (12:00, 18:00)]

            # Услуга в начале окна:
            split_window_by_service(9:00, 18:00, 9:00, 11:00)
            # → [(11:00, 18:00)]
        """
        remaining: list[tuple[datetime, datetime]] = []

        # Часть до услуги
        if service_start > window_start:
            remaining.append((window_start, service_start))

        # Часть после услуги
        if service_end < window_end:
            remaining.append((service_end, window_end))

        return remaining

    # ---------------------------------------------------------------------------
    # Внутренние вспомогательные методы
    # ---------------------------------------------------------------------------

    def _merge_intervals(self, intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
        """
        Мёрджит пересекающиеся или смежные интервалы.
        Возвращает отсортированный список непересекающихся интервалов.

        Внутренний метод. Используется в merge_free_windows.
        """
        if not intervals:
            return []

        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        merged: list[tuple[datetime, datetime]] = [sorted_intervals[0]]

        for start, end in sorted_intervals[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                # Пересечение — расширяем текущий блок
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged

    def _align_to_grid(self, target: datetime, grid_origin: datetime) -> datetime:
        """
        Выравнивает target к ближайшему шагу сетки относительно grid_origin.
        Возвращает первый момент сетки >= target.

        Внутренний метод. Используется для выравнивания min_start к сетке.

        Пример (шаг 30 мин, origin 9:00, target 9:17):
            → 9:30  (ближайший шаг >= 9:17)
        """
        delta_seconds = (target - grid_origin).total_seconds()
        step_seconds = self._step_delta.total_seconds()

        if delta_seconds <= 0:
            return grid_origin

        # Количество полных шагов
        full_steps = int(delta_seconds / step_seconds)
        aligned = grid_origin + timedelta(seconds=full_steps * step_seconds)

        if aligned < target:
            aligned += self._step_delta

        return aligned
