"""
codex_tools.codex_calendar.engine
=================================
Универсальный генератор календаря.
Не зависит от Django.
"""

import calendar
from datetime import date
from typing import Any

from holidays.countries import Germany


class CalendarEngine:
    """
    Генератор матрицы дней для календаря.

    Используется для отрисовки UI (сайт, бот).
    """

    @staticmethod
    def get_month_matrix(
        year: int,
        month: int,
        today: date,
        selected_date: date | None = None,
        holidays_subdiv: str = "ST",  # По умолчанию Саксония-Анхальт
    ) -> list[dict[str, Any]]:
        """
        Генерирует список дней для сетки календаря.

        Args:
            year: Год.
            month: Месяц.
            today: Текущая дата (для определения прошлого).
            selected_date: Выбранная дата (для статуса 'active').
            holidays_subdiv: Регион Германии для праздников.

        Returns:
            Список словарей с данными о днях.
        """
        de_holidays = Germany(subdiv=holidays_subdiv, years=year)

        cal = calendar.Calendar(firstweekday=0)  # Пн - первый день
        month_days = cal.itermonthdays(year, month)

        result: list[dict[str, Any]] = []
        for day_num in month_days:
            if day_num == 0:
                result.append({"num": "", "status": "empty"})
                continue

            calc_date = date(year, month, day_num)
            weekday = calc_date.weekday()

            # Базовый статус
            status = "available"

            if calc_date < today or weekday == 6:
                status = "disabled"
            elif calc_date in de_holidays:
                status = "holiday"

            if selected_date and calc_date == selected_date:
                status = "active"

            day_data: dict[str, Any] = {
                "num": str(day_num),
                "date": calc_date.isoformat(),
                "status": status,
                "is_holiday": calc_date in de_holidays,
                "weekday": weekday,
            }
            result.append(day_data)

        return result

    @staticmethod
    def get_month_label(year: int, month: int, locale: str = "ru") -> str:
        """Возвращает название месяца и год."""
        month_names_ru = {
            1: "Январь",
            2: "Февраль",
            3: "Март",
            4: "Апрель",
            5: "Май",
            6: "Июнь",
            7: "Июль",
            8: "Август",
            9: "Сентябрь",
            10: "Октябрь",
            11: "Ноябрь",
            12: "Декабрь",
        }
        # Можно добавить другие языки (de, en) при необходимости
        name = month_names_ru.get(month, "")
        return f"{name} {year}"
