"""
codexn_tools.booking.exceptions
=================================
Кастомные исключения движка бронирования.

Иерархия:
    BookingEngineError (базовое)
    ├── NoAvailabilityError      — нет свободных слотов для запроса
    ├── InvalidServiceDurationError — некорректная длительность услуги
    ├── InvalidBookingDateError  — некорректная/недопустимая дата
    └── MasterNotAvailableError  — конкретный мастер недоступен

Использование в сервисном слое:
    from codexn_tools.booking.exceptions import NoAvailabilityError

    try:
        result = finder.find(request, availability)
        if not result.has_solutions:
            raise NoAvailabilityError(
                date=request.booking_date,
                service_ids=[s.service_id for s in request.service_requests],
            )
    except NoAvailabilityError as e:
        # Django-view поймает и вернёт понятное сообщение пользователю
        return render(request, "booking/no_slots.html", {"error": str(e)})

Импорт:
    from codexn_tools.booking.exceptions import (
        BookingEngineError,
        NoAvailabilityError,
        InvalidServiceDurationError,
        InvalidBookingDateError,
        MasterNotAvailableError,
    )
"""

from datetime import date


class BookingEngineError(Exception):
    """
    Базовое исключение движка бронирования.

    Все остальные исключения наследуются от него.
    Django-view может поймать BookingEngineError для единой обработки
    всех ошибок движка.

    Пример:
        try:
            result = service.book(...)
        except BookingEngineError as e:
            messages.error(request, str(e))
            return redirect("booking:wizard")
    """

    default_message: str = "Ошибка системы бронирования"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class NoAvailabilityError(BookingEngineError):
    """
    Движок не нашёл ни одного варианта расписания для запроса.

    Вызывается когда ChainFinder.find() вернул пустой EngineResult.
    В Django-view переводится в user-friendly сообщение.

    Атрибуты:
        booking_date: Дата на которую искали.
        service_ids: Список id услуг из запроса.

    Пример:
        raise NoAvailabilityError(
            booking_date=date(2024, 5, 10),
            service_ids=["5", "12"],
        )
        # str(e) → "Нет свободных слотов на 10.05.2024 для выбранных услуг."
    """

    default_message = "К сожалению, на выбранную дату нет доступных слотов для этих услуг."

    def __init__(
        self,
        booking_date: date | None = None,
        service_ids: list[str] | None = None,
        message: str | None = None,
    ) -> None:
        self.booking_date = booking_date
        self.service_ids = service_ids or []

        if message:
            final_message = message
        elif booking_date:
            date_str = booking_date.strftime("%d.%m.%Y")
            final_message = f"Нет свободных слотов на {date_str} для выбранных услуг. Попробуйте выбрать другую дату."
        else:
            final_message = self.default_message

        super().__init__(final_message)


class InvalidServiceDurationError(BookingEngineError):
    """
    Некорректная длительность услуги.

    Вызывается если duration_minutes <= 0 или превышает допустимый максимум.

    Атрибуты:
        service_id: Id проблемной услуги.
        duration_minutes: Переданное значение длительности.

    Пример:
        raise InvalidServiceDurationError(service_id="5", duration_minutes=0)
        # str(e) → "Услуга 5: некорректная длительность 0 мин."
    """

    default_message = "Некорректная длительность услуги."

    def __init__(
        self,
        service_id: str | None = None,
        duration_minutes: int | None = None,
        message: str | None = None,
    ) -> None:
        self.service_id = service_id
        self.duration_minutes = duration_minutes

        if message:
            final_message = message
        elif service_id is not None and duration_minutes is not None:
            final_message = (
                f"Услуга {service_id}: некорректная длительность {duration_minutes} мин. "
                "Длительность должна быть больше 0."
            )
        else:
            final_message = self.default_message

        super().__init__(final_message)


class InvalidBookingDateError(BookingEngineError):
    """
    Дата бронирования недопустима.

    Примеры причин:
        - Дата в прошлом
        - Дата дальше max_advance_days
        - Салон закрыт в этот день

    Атрибуты:
        booking_date: Проблемная дата.
        reason: Человекочитаемое пояснение.

    Пример:
        raise InvalidBookingDateError(
            booking_date=date(2020, 1, 1),
            reason="Дата в прошлом",
        )
    """

    default_message = "Выбранная дата недоступна для записи."

    def __init__(
        self,
        booking_date: date | None = None,
        reason: str | None = None,
        message: str | None = None,
    ) -> None:
        self.booking_date = booking_date
        self.reason = reason

        if message:
            final_message = message
        elif booking_date and reason:
            date_str = booking_date.strftime("%d.%m.%Y")
            final_message = f"Дата {date_str} недоступна: {reason}."
        elif booking_date:
            date_str = booking_date.strftime("%d.%m.%Y")
            final_message = f"Дата {date_str} недоступна для записи."
        else:
            final_message = self.default_message

        super().__init__(final_message)


class SlotAlreadyBookedError(BookingEngineError):
    """
    Слот был свободен при показе, но занят к моменту подтверждения бронирования.

    Race condition: клиент A и клиент B одновременно смотрят один слот.
    A нажимает "Записаться" первым → B получает эту ошибку.

    Django-view должен показать клиенту B сообщение:
    "Этот слот только что заняли. Выберите другое время."

    Атрибуты:
        master_id: Id мастера.
        service_id: Id услуги.
        booking_date: Дата бронирования.
        slot_time: Выбранное время (строка "HH:MM").

    Пример:
        raise SlotAlreadyBookedError(
            master_id="3",
            service_id="5",
            booking_date=date(2024, 5, 10),
            slot_time="14:00",
        )
        # str(e) → "Слот 14:00 10.05.2024 был занят. Выберите другое время."
    """

    default_message = "Выбранный слот был занят. Пожалуйста, выберите другое время."

    def __init__(
        self,
        master_id: str | None = None,
        service_id: str | None = None,
        booking_date: date | None = None,
        slot_time: str | None = None,
        message: str | None = None,
    ) -> None:
        self.master_id = master_id
        self.service_id = service_id
        self.booking_date = booking_date
        self.slot_time = slot_time

        if message:
            final_message = message
        elif slot_time and booking_date:
            date_str = booking_date.strftime("%d.%m.%Y")
            final_message = f"Слот {slot_time} на {date_str} был занят пока вы оформляли запись. Выберите другое время."
        else:
            final_message = self.default_message

        super().__init__(final_message)


class ChainBuildError(BookingEngineError):
    """
    Движок не смог собрать цепочку для всех услуг запроса.

    Отличается от NoAvailabilityError: здесь цепочка ЧАСТИЧНО собралась,
    но не до конца (нарушение ограничений, несовместимые услуги и т.д.).

    Используется когда:
        - max_chain_duration_minutes превышен
        - Услуги несовместимы (будущее: excludes/tags)
        - group_size > доступных параллельных слотов

    Атрибуты:
        failed_at_index: Индекс услуги (в service_requests) на которой сборка упала.
        reason: Техническая причина (для логов).

    Пример:
        raise ChainBuildError(
            failed_at_index=2,
            reason="max_chain_duration_minutes=180 exceeded at service 'Покраска'",
        )
    """

    default_message = "Не удалось подобрать расписание для всех выбранных услуг."

    def __init__(
        self,
        failed_at_index: int | None = None,
        reason: str | None = None,
        message: str | None = None,
    ) -> None:
        self.failed_at_index = failed_at_index
        self.reason = reason

        if message:
            final_message = message
        elif reason:
            final_message = f"Не удалось собрать цепочку: {reason}."
        else:
            final_message = self.default_message

        super().__init__(final_message)


class MasterNotAvailableError(BookingEngineError):
    """
    Конкретный мастер недоступен для бронирования.

    Используется в режиме MASTER_LOCKED когда выбранный мастер
    не работает в этот день или его расписание пустое.

    Атрибуты:
        master_id: Id мастера.
        booking_date: Дата на которую пытались записаться.

    Пример:
        raise MasterNotAvailableError(master_id="3", booking_date=date(2024,5,10))
        # str(e) → "Мастер недоступен на 10.05.2024."
    """

    default_message = "Выбранный мастер недоступен на эту дату."

    def __init__(
        self,
        master_id: str | None = None,
        booking_date: date | None = None,
        message: str | None = None,
    ) -> None:
        self.master_id = master_id
        self.booking_date = booking_date

        if message:
            final_message = message
        elif booking_date:
            date_str = booking_date.strftime("%d.%m.%Y")
            final_message = f"Мастер недоступен на {date_str}. Попробуйте выбрать другую дату."
        else:
            final_message = self.default_message

        super().__init__(final_message)
