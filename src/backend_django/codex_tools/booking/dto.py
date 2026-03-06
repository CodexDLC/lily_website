"""
codexn_tools.booking.dto
=========================
Pydantic v2 DTO (Data Transfer Objects) для движка бронирования.

Все модели immutable (frozen=True) — движок не мутирует входные данные.
Никаких Django-импортов. Только Python stdlib + pydantic.

Импорт:
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
    Запрос на одну услугу в рамках бронирования.

    Движок не знает о конкретных мастерах — только о тех,
    кто *способен* выполнить данную услугу (possible_master_ids).
    Подбор конкретного мастера — задача ChainFinder.

    Поля:
        service_id (str):
            Уникальный идентификатор услуги. Строка для универсальности
            (может быть "5", "uuid-xxx", "manicure" — не важно).

        duration_minutes (int):
            Длительность услуги в минутах. Должна быть > 0.

        min_gap_after_minutes (int):
            Минимальная пауза (мин) после этой услуги перед следующей
            в цепочке. По умолчанию 0 (без паузы).
            Пример: после покраски нужно 30 мин ожидания → min_gap_after_minutes=30

        possible_master_ids (list[str]):
            Список id мастеров, которые умеют выполнять эту услугу.
            Движок выбирает из этого списка свободного мастера.
            Для MASTER_LOCKED содержит ровно один элемент.

        parallel_group (str | None):
            Метка группы параллельного выполнения.
            Услуги с одинаковым parallel_group могут выполняться одновременно
            разными мастерами (overlap_allowed=True должен быть в запросе).
            None = услуга выполняется независимо (стандартное поведение).

            Пример — педикюр и маникюр параллельно:
                svc_mani = ServiceRequest(..., parallel_group="session_1")
                svc_pedi = ServiceRequest(..., parallel_group="session_1")
                # Обе услуги могут стартовать в одно время у разных мастеров.

            Пример — консультация → процедуры параллельно:
                svc_consult = ServiceRequest(..., parallel_group=None)   # сначала
                svc_a = ServiceRequest(..., parallel_group="procedures") # потом параллельно
                svc_b = ServiceRequest(..., parallel_group="procedures") # потом параллельно

    Пример:
        ServiceRequest(
            service_id="5",
            duration_minutes=60,
            possible_master_ids=["1", "3", "7"],
        )

    Пример с параллельной группой:
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
        """Суммарное время которое блокирует мастера: duration + gap после."""
        return self.duration_minutes + self.min_gap_after_minutes


class BookingEngineRequest(BaseModel, frozen=True):
    """
    Входной запрос к движку. Описывает ЧТО нужно забронировать.

    Поля:
        service_requests (list[ServiceRequest]):
            Список услуг для бронирования. Порядок важен для SINGLE_DAY —
            движок будет планировать их в указанном порядке.
            Минимум 1 услуга.

        booking_date (date):
            Дата бронирования. Используется для SINGLE_DAY и MASTER_LOCKED.
            Для MULTI_DAY — дата первой услуги (остальные — отдельно, future).

        mode (BookingMode):
            Режим работы движка. По умолчанию SINGLE_DAY.

        overlap_allowed (bool):
            Разрешить параллельное выполнение услуг разными мастерами.
            False (по умолчанию) — каждая следующая услуга начинается только после окончания
            предыдущей (строго последовательно, полезно для авто-сервисов
            и других пайплайнов где клиент переходит от мастера к мастеру).
            True — мастера работают независимо, услуги могут
            начинаться одновременно (педикюр + ресницы в одно время).

        group_size (int):
            DEPRECATED. Используйте дублирование ServiceRequest с parallel_group.
            Количество клиентов в группе. По умолчанию 1.

        max_chain_duration_minutes (int | None):
            Максимальная суммарная длительность всей записи в минутах
            (от начала первой до конца последней услуги).
            None = без ограничения.
            Пример: max_chain_duration_minutes=240 → запись не длиннее 4 часов.

        days_gap (list[int] | None):
            Для MULTI_DAY: смещение в днях для каждой услуги от booking_date.
            [0, 0, 7] → первые две услуги в booking_date, третья через 7 дней.
            None = все услуги в один день (SINGLE_DAY поведение).
            ВАЖНО: используется только в MULTI_DAY режиме (пока не реализован).

    Пример:
        BookingEngineRequest(
            service_requests=[svc_manicure, svc_pedicure],
            booking_date=date(2024, 5, 10),
            mode=BookingMode.SINGLE_DAY,
        )

    Пример с параллельными услугами:
        BookingEngineRequest(
            service_requests=[svc_manicure, svc_pedicure],
            booking_date=date(2024, 5, 10),
            overlap_allowed=True,   # маникюр и педикюр одновременно
        )

    Пример с ограничением длительности:
        BookingEngineRequest(
            service_requests=[svc_a, svc_b, svc_c],
            booking_date=date(2024, 5, 10),
            max_chain_duration_minutes=180,  # не более 3 часов
        )
    """

    service_requests: list[ServiceRequest] = Field(min_length=1, description="Минимум одна услуга")
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
        """Суммарная длительность всех услуг (без gap-пауз)."""
        return sum(s.duration_minutes for s in self.service_requests)

    @property
    def total_block_minutes(self) -> int:
        """
        Суммарное время блокировки включая паузы между услугами.
        Используется для быстрой проверки: влезает ли цепочка в окно.
        """
        return sum(s.total_block_minutes for s in self.service_requests)


# ---------------------------------------------------------------------------
# Данные доступности (подготавливаются адаптером)
# ---------------------------------------------------------------------------


class MasterAvailability(BaseModel, frozen=True):
    """
    Свободные временные окна мастера на заданную дату.
    Подготавливается адаптером (DjangoAvailabilityAdapter),
    движок их только читает — не ходит в БД.

    Поля:
        master_id (str):
            Идентификатор мастера (строка для универсальности).

        free_windows (list[tuple[datetime, datetime]]):
            Список свободных окон в формате [(window_start, window_end), ...].
            Окна уже очищены от занятых слотов и перерывов.
            Отсортированы по времени начала.

        buffer_between_minutes (int):
            Буфер между клиентами у этого мастера.
            Учитывается при подборе следующего слота.

    Пример:
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
        """Проверяет что каждое окно: start < end."""
        for start, end in self.free_windows:
            if start >= end:
                raise ValueError(f"Мастер {self.master_id}: start={start} >= end={end}")
        return self


# ---------------------------------------------------------------------------
# Выходные DTO (результат работы движка)
# ---------------------------------------------------------------------------


class SingleServiceSolution(BaseModel, frozen=True):
    """
    Найденный слот для одной услуги в цепочке.

    Поля:
        service_id (str): Id услуги из ServiceRequest.
        master_id (str): Id выбранного мастера.
        start_time (datetime): Начало выполнения услуги.
        end_time (datetime): Конец выполнения услуги (без gap).
        gap_end_time (datetime): Конец с учётом паузы (мастер занят до этого момента).
    """

    service_id: str
    master_id: str
    start_time: datetime
    end_time: datetime
    gap_end_time: datetime  # end_time + min_gap_after_minutes

    @property
    def duration_minutes(self) -> int:
        """Фактическая длительность услуги в минутах."""
        return int((self.end_time - self.start_time).total_seconds() / 60)


class BookingChainSolution(BaseModel, frozen=True):
    """
    Одно полное решение для всего запроса (набор слотов для всех услуг).
    Найдено движком. Гарантирует отсутствие конфликтов между услугами.

    Поля:
        items (list[SingleServiceSolution]):
            Список слотов в порядке выполнения услуг.

        score (float):
            Оценка качества решения. По умолчанию 0.0.
            Более высокий score = более предпочтительное решение.
            Пример использования:
                - предпочтительный мастер → score += 10
                - минимальный простой между услугами → score += 2 за каждый час
                - один мастер на несколько услуг → score += 5
            Используется при сортировке и выборе result.best.
            Установить можно через ChainFinder или внешний скорер.

    Свойства:
        starts_at: время начала первой услуги
        ends_at:   время конца последней услуги
        span_minutes: общее время от начала первой до конца последней
    """

    items: list[SingleServiceSolution] = Field(min_length=1)
    score: float = Field(default=0.0, description="Оценка качества решения")

    @property
    def starts_at(self) -> datetime:
        """Начало первой услуги в цепочке."""
        return min(s.start_time for s in self.items)

    @property
    def ends_at(self) -> datetime:
        """Конец последней услуги (без gap)."""
        return max(s.end_time for s in self.items)

    @property
    def span_minutes(self) -> int:
        """Общее время от начала первой до конца последней услуги."""
        return int((self.ends_at - self.starts_at).total_seconds() / 60)

    def to_display(self) -> dict[str, Any]:
        """
        Конвертирует решение в dict для UI/сериализации.
        Возвращает: {service_id: {master_id, start, end}, ...}
        """
        return {
            item.service_id: {
                "master_id": item.master_id,
                "start": item.start_time.strftime("%H:%M"),
                "end": item.end_time.strftime("%H:%M"),
            }
            for item in self.items
        }


class EngineResult(BaseModel, frozen=True):
    """
    Результат работы движка. Возвращается ChainFinder.find().

    Поля:
        mode (BookingMode): Режим в котором был выполнен поиск.
        solutions (list[BookingChainSolution]):
            Найденные варианты расписания. Пустой список = ничего не нашли.
            После BookingScorer.score() — отсортированы по score DESC.
            По умолчанию (без скорера) — по времени начала первой услуги.

    Свойства:
        has_solutions (bool): Быстрая проверка наличия результатов.
        best (BookingChainSolution | None): Первый вариант (ранний или лучший по score).
        best_scored (BookingChainSolution | None): Вариант с максимальным score.

    Пример использования без скорера (первый по времени):
        result = ChainFinder().find(request, availability)
        if result.has_solutions:
            print(result.best.starts_at)

    Пример с BookingScorer (первый по качеству):
        result = BookingScorer(preferred_master_ids=["3"]).score(result)
        print(result.best.score)        # наивысший score
        print(result.best_scored.score) # то же самое
    """

    mode: BookingMode
    solutions: list[BookingChainSolution] = Field(default_factory=list)

    @property
    def has_solutions(self) -> bool:
        """True если движок нашёл хотя бы одно решение."""
        return len(self.solutions) > 0

    @property
    def best(self) -> BookingChainSolution | None:
        """
        Первый вариант в списке решений.
        - Без скорера: самый ранний по времени начала.
        - После BookingScorer.score(): с наивысшим score.
        None если решений нет.
        """
        return self.solutions[0] if self.solutions else None

    @property
    def best_scored(self) -> BookingChainSolution | None:
        """
        Вариант с максимальным score среди всех решений.

        Отличается от best если scorer ещё не применялся —
        в этом случае best = earliest, best_scored = highest_score.
        После BookingScorer.score() они совпадают (список уже отсортирован).

        None если решений нет.
        """
        if not self.solutions:
            return None
        return max(self.solutions, key=lambda s: s.score)

    def get_unique_start_times(self) -> list[str]:
        """
        Возвращает список уникальных времён начала первой услуги.
        Используется для отображения сетки слотов в UI.
        Формат: ["09:00", "09:30", "10:00", ...]
        """
        times = {s.starts_at.strftime("%H:%M") for s in self.solutions}
        return sorted(times)


# ---------------------------------------------------------------------------
# Waitlist DTO (результат find_nearest / waitlist-уведомлений)
# ---------------------------------------------------------------------------


class WaitlistEntry(BaseModel, frozen=True):
    """
    Ближайший доступный слот для уведомления клиента из листа ожидания.

    Возвращается ChainFinder.find_nearest() через вспомогательный сервис
    или waitlist-воркером при освобождении слота.

    Поля:
        available_date (date): Дата когда слот стал доступен.
        available_time (str): Время начала первой услуги ("HH:MM").
        solution (BookingChainSolution): Полное найденное решение.
        days_from_request (int): Через сколько дней от исходной даты запроса.

    Пример использования:
        # В waitlist-воркере, когда отменили запись:
        result = finder.find_nearest(request, get_avail, search_from=original_date)
        if result.has_solutions:
            entry = WaitlistEntry.from_engine_result(result, original_date)
            notify_client(entry)  # отправить email/telegram

    Пример создания:
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
        Создаёт WaitlistEntry из EngineResult найденного find_nearest().

        Args:
            result: EngineResult с хотя бы одним решением.
            original_date: Исходная дата запроса (для расчёта days_from_request).

        Returns:
            WaitlistEntry или None если result пустой.
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
