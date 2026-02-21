from typing import Any


class TableFormatter:
    """
    Утилита для форматирования данных в текстовые таблицы.
    """

    @staticmethod
    def format_table(headers: list[str], rows: list[list[Any]]) -> str:
        """
        Форматирует данные в ASCII-таблицу.

        Пример:
        +-------------------+-------+-------+
        | Категория         | Всего | Новых |
        +-------------------+-------+-------+
        | Бронирование      | 15    | 3     |
        +-------------------+-------+-------+
        """
        if not rows:
            return "Нет данных для отображения."

        # Вычисляем ширину колонок
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        # Линия-разделитель
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

        # Форматируем строки
        def format_row(data):
            return "| " + " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(data)) + " |"

        result = [
            separator,
            format_row(headers),
            separator,
        ]

        for row in rows:
            result.append(format_row(row))

        result.append(separator)
        return "\n".join(result)
