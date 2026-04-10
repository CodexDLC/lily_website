import random
import time
from datetime import date, datetime, timedelta

import pytest
from codex_tools.booking import (
    BookingEngineRequest,
    BookingMode,
    ChainFinder,
    MasterAvailability,
    ServiceRequest,
)


@pytest.mark.unit
def test_extreme_chain_performance():
    """
    Стресс-тест для ChainFinder (Backtracking).

    Сценарий (Worst Case - "Лабиринт с тупиками"):
    - 5 услуг по 60 минут.
    - 5 мастеров.
    - У мастеров много окон, которые выглядят подходящими, но ведут в тупик на 3-4 шаге.
    - Алгоритм вынужден перебирать сотни комбинаций.

    Цель: Время выполнения < 1.0 сек (при полном переборе).
    """
    # 1. Setup Data
    target_date = date(2024, 5, 20)

    master_ids = ["m1", "m2", "m3", "m4", "m5"]

    availability = {}
    for _, mid in enumerate(master_ids):
        windows = []
        # Генерируем "ловушки" - окна по 60 минут, которые подходят локально,
        # но не стыкуются глобально.
        # Например, каждый час с 9 до 18.
        for hour in range(9, 18):
            start = datetime(2024, 5, 20, hour, 0)
            end = start + timedelta(minutes=60)
            windows.append((start, end))

        # Сортируем окна (ChainFinder ожидает хронологию)
        windows.sort(key=lambda x: x[0])

        availability[mid] = MasterAvailability(master_id=mid, free_windows=windows, buffer_between_minutes=0)

    # Создаем запрос: 5 услуг.
    # Хитрость: мы ищем ВСЕ решения.
    # Так как у каждого мастера куча окон, комбинаций будет тысячи.
    # Но большинство из них не состыкуются в цепочку длиной 5 (из-за overlap_allowed=False).
    # Например:
    # Услуга 1: m1 (09:00-10:00)
    # Услуга 2: m2 (10:00-11:00) ...
    # Услуга 5: m5 (13:00-14:00) - ОК.
    # А вот:
    # Услуга 1: m1 (17:00-18:00) -> Услуга 2 не влезает (конец дня).

    service_requests = []
    for i in range(5):
        # Перемешиваем порядок мастеров, чтобы алгоритм не шел по "идеальному" пути m1, m2...
        shuffled_masters = list(master_ids)
        random.shuffle(shuffled_masters)

        service_requests.append(
            ServiceRequest(
                service_id=f"s{i}", duration_minutes=60, possible_master_ids=shuffled_masters, min_gap_after_minutes=0
            )
        )

    request = BookingEngineRequest(
        service_requests=service_requests, booking_date=target_date, mode=BookingMode.SINGLE_DAY, overlap_allowed=False
    )

    finder = ChainFinder(step_minutes=30)

    # 2. Measure Execution Time
    start_time = time.perf_counter()

    # Ищем 1000 решений. Это заставит алгоритм перелопатить дерево.
    result = finder.find(request, availability, max_solutions=1000)

    end_time = time.perf_counter()
    duration = end_time - start_time

    # 3. Assertions
    print(f"\nStress Performance: Found {len(result.solutions)} solutions in {duration:.4f} sec")

    assert result.has_solutions

    # Лимит 1.0 сек для полного перебора (это Python, не C++)
    assert duration < 1.0, f"Too slow! Took {duration:.4f}s"


@pytest.mark.unit
def test_parallel_chain_performance():
    """
    Стресс-тест для параллельного выполнения (overlap_allowed=True).
    """
    target_date = date(2024, 5, 20)
    work_start = datetime(2024, 5, 20, 9, 0)
    work_end = datetime(2024, 5, 20, 21, 0)
    master_ids = ["m1", "m2", "m3", "m4", "m5"]

    availability = {mid: MasterAvailability(master_id=mid, free_windows=[(work_start, work_end)]) for mid in master_ids}

    service_requests = [
        ServiceRequest(service_id=f"s{i}", duration_minutes=60, possible_master_ids=master_ids) for i in range(5)
    ]

    request = BookingEngineRequest(
        service_requests=service_requests,
        booking_date=target_date,
        mode=BookingMode.SINGLE_DAY,
        overlap_allowed=True,  # Параллельное выполнение
    )

    finder = ChainFinder(step_minutes=30)

    start_time = time.perf_counter()
    result = finder.find(request, availability, max_solutions=50)
    end_time = time.perf_counter()

    duration = end_time - start_time
    print(f"\nParallel Performance: Found {len(result.solutions)} solutions in {duration:.4f} sec")

    assert result.has_solutions
    assert duration < 0.1  # Должно быть еще быстрее


@pytest.mark.unit
def test_parallel_group_logic():
    """
    Тест логики parallel_group (например, парный маникюр).
    """
    target_date = date(2024, 5, 20)

    # Master 1: Free all day
    m1_avail = MasterAvailability(
        master_id="m1", free_windows=[(datetime(2024, 5, 20, 9, 0), datetime(2024, 5, 20, 18, 0))]
    )

    # Master 2: Busy 10:00-11:00 (so free 9-10, 11-18)
    m2_avail = MasterAvailability(
        master_id="m2",
        free_windows=[
            (datetime(2024, 5, 20, 9, 0), datetime(2024, 5, 20, 10, 0)),
            (datetime(2024, 5, 20, 11, 0), datetime(2024, 5, 20, 18, 0)),
        ],
    )

    availability = {"m1": m1_avail, "m2": m2_avail}

    service_requests = [
        ServiceRequest(
            service_id="mani_1", duration_minutes=60, possible_master_ids=["m1", "m2"], parallel_group="couple"
        ),
        ServiceRequest(
            service_id="mani_2", duration_minutes=60, possible_master_ids=["m1", "m2"], parallel_group="couple"
        ),
    ]

    request = BookingEngineRequest(
        service_requests=service_requests,
        booking_date=target_date,
        mode=BookingMode.SINGLE_DAY,
        overlap_allowed=True,  # Важно!
    )

    finder = ChainFinder(step_minutes=60)  # Шаг час для простоты
    result = finder.find(request, availability)

    assert result.has_solutions

    # Проверяем первое решение
    sol = result.best
    item1 = sol.items[0]
    item2 = sol.items[1]

    # Должны начаться в одно время
    assert item1.start_time == item2.start_time

    # Проверим, что 10:00 НЕ предлагается
    times = result.get_unique_start_times()
    assert "10:00" not in times
    assert "09:00" in times
    assert "11:00" in times

    # Проверим, что мастера разные
    assert item1.master_id != item2.master_id
