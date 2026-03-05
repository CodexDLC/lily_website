"""
codexn_tools.booking.modes
==========================
Режимы работы движка бронирования.

Импорт:
    from codexn_tools.booking import BookingMode
"""

from enum import StrEnum


class BookingMode(StrEnum):
    """
    Режим работы ChainFinder.

    SINGLE_DAY:
        Все услуги из запроса укладываются в один день.
        Движок ищет непрерывную (или с допустимыми паузами) цепочку слотов.
        Самый частый режим — клиент хочет сделать несколько услуг за одно посещение.

    MULTI_DAY:
        Каждая услуга может быть запланирована на отдельный день.
        Заглушка — реализуется в следующей итерации.
        find() с этим режимом вернёт EngineResult(solutions=[]).

    MASTER_LOCKED:
        Запись к конкретному мастеру (например, с его личной страницы на сайте).
        Работает как SINGLE_DAY, но ServiceRequest.possible_master_ids
        содержит ровно один id — id выбранного мастера.
        Движок не подбирает мастера — использует только указанного.

    Пример:
        mode = BookingMode.SINGLE_DAY
        mode = BookingMode("single_day")   # тоже работает
    """

    SINGLE_DAY = "single_day"
    MULTI_DAY = "multi_day"
    MASTER_LOCKED = "master_locked"
