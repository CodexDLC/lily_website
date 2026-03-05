"""
codex_tools.common.text
=======================
Универсальные инструменты для работы с текстом.
Не зависит от Django.
"""


def normalize_name(name: str) -> str:
    """
    Приводит имя/фамилию к стандартному виду: 'Иван' или 'Иван-Иванович'.
    """
    if not name:
        return ""

    # Убираем лишние пробелы и делаем Capitalize
    parts = name.strip().split("-")
    normalized_parts = [p.strip().capitalize() for p in parts if p.strip()]

    return "-".join(normalized_parts)


def clean_string(text: str) -> str:
    """Убирает лишние пробелы и невидимые символы."""
    if not text:
        return ""
    return " ".join(text.split())
