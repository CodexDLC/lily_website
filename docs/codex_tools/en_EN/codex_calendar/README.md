# 🗓️ Codex Calendar

[⬅️ Back to Docs Root](../../README.md)

The `codex_calendar` module provides a universally acceptable framework-agnostic calendar grid generator. It solves the trivial but frequently recurring task of building the current month's matrix for UI rendering or Telegram bots.

## Why is it a separate module?
Experience shows that generating a calendar grid (accounting for first days of the week, empty buffer cells at the start/end of the month, and weekends/holidays) is often written from scratch in every project.

The `CalendarEngine` centralizes this logic into a single dependency.
The main architectural decision here is that the calendar returns a **universal dictionary of states** for each day (`available`, `disabled`, `holiday`), which any frontend client can render with its own styling.

## `CalendarEngine`

The heart of the module is the `CalendarEngine` located in `engine.py`. Its purpose is to output robust month-views for UIs across websites, telegram bots, and mobile apps.

### Key Features
1. **Holistic Arrays**: Iterates through complete visual weeks (`calendar.Calendar`), padding out-of-month dates with empty spaces to maintain consistent matrix alignment.
2. **State Resolution**: Tags each day with its state: `available`, `disabled` (past days or specific non-working days), `holiday`, or `active`.
3. **Locale Support**: Integrates with the `holidays` Python package to inject dynamic national public holidays into the matrix.

### Usage Example
```python
from codex_tools.codex_calendar.engine import CalendarEngine
from datetime import date

engine = CalendarEngine()
matrix = engine.get_month_matrix(
    year=2024,
    month=5,
    today=date.today(),
    holidays_subdiv="ST" # regional holiday code (e.g. Germany -> Saxony-Anhalt)
)
```
