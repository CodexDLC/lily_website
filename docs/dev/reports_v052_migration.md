# Reports — Migration to ReportPageData (codex-django v0.5.2)

Migrate analytics reports to use the updated codex-django `ReportPageData`
contract, and wire up the new `year` and `custom` period filters.

---

## What changed in codex-django v0.5.2

- `resolve_report_period` now accepts `year` and `custom` period keys.
- `custom` reads `date_from` / `date_to` kwargs (ISO strings or `date` objects).
  Invalid or inverted bounds fall back to `month`.
- `_report_filters.html` now contains a `<form method="get">` with two date
  inputs and a calendar-range submit button (📅).

---

## Files to touch

### 1. View (`apps/analytics/views.py` or equivalent)

```python
from codex_django.cabinet.reports import resolve_report_period

period     = request.GET.get("period", "month")
date_from  = request.GET.get("date_from")
date_to    = request.GET.get("date_to")
active_tab = request.GET.get("tab", "revenue")

resolved = resolve_report_period(period, date_from=date_from, date_to=date_to)
report   = LilyReportsService.build(tab=active_tab, period=resolved)

context = {
    "report":        report,
    "active_period": resolved.key,
    "date_from":     resolved.date_from.isoformat(),
    "date_to":       resolved.date_to.isoformat(),
}
```

### 2. Template (`analytics/reports.html`)

```html
{% include "cabinet/includes/_report_filters.html" with
    report_tabs=report.tabs
    period_options=report.period_options
    active_tab=report.active_tab
    active_period=report.active_period
    date_from=date_from
    date_to=date_to %}

{% include "cabinet/reports/chart.html" with chart=report.chart %}
{% include "cabinet/reports/table.html" with table=report.table %}
```

Убрать старые переменные `revenue_chart_data`, `revenue_table_data` и т.д.

### 3. Period options — добавить Year

```python
PERIOD_OPTIONS = [
    {"key": "week",    "label": "Week"},
    {"key": "month",   "label": "Month"},
    {"key": "quarter", "label": "Quarter"},
    {"key": "year",    "label": "Year"},   # ← add
]
```

### 4. LilyReportsService — принимать ReportPeriod

```python
def build(self, *, tab: str, period: ReportPeriod) -> ReportPageData:
    qs = Booking.objects.filter(
        date__gte=period.date_from,
        date__lte=period.date_to,
    )
```
