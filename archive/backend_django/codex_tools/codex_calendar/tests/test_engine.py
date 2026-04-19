"""
Unit tests for codex_tools.codex_calendar.engine.CalendarEngine.
Tests date matrix generation, status assignment, and month label formatting.
"""

from datetime import date

import pytest
from codex_tools.codex_calendar.engine import CalendarEngine


@pytest.mark.unit
class TestCalendarEngineGetMonthMatrix:
    def test_returns_list(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 5, 1))
        assert isinstance(result, list)

    def test_non_empty_result(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 5, 1))
        assert len(result) > 0

    def test_empty_padding_cells_have_empty_num(self):
        # Any month — padding cells should have num=""
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 5, 1))
        for cell in result:
            if cell["status"] == "empty":
                assert cell["num"] == ""

    def test_real_days_have_numeric_string_num(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 5, 1))
        real_days = [c for c in result if c["status"] != "empty"]
        assert all(c["num"].isdigit() for c in real_days)

    def test_past_days_are_disabled(self):
        today = date(2024, 5, 15)
        result = CalendarEngine.get_month_matrix(2024, 5, today=today)
        for cell in result:
            if cell.get("date"):
                cell_date = date.fromisoformat(cell["date"])
                if cell_date < today:
                    assert cell["status"] == "disabled", (
                        f"Expected 'disabled' for past date {cell_date}, got '{cell['status']}'"
                    )

    def test_sundays_are_disabled(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 4, 1))
        for cell in result:
            if cell.get("date") and cell.get("weekday") == 6:
                assert cell["status"] == "disabled", f"Sunday {cell['date']} should be disabled"

    def test_selected_date_gets_active_status(self):
        today = date(2024, 5, 1)
        selected = date(2024, 5, 20)
        result = CalendarEngine.get_month_matrix(2024, 5, today=today, selected_date=selected)
        active_cells = [c for c in result if c.get("status") == "active"]
        assert len(active_cells) == 1
        assert active_cells[0]["date"] == "2024-05-20"

    def test_no_active_without_selected_date(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 5, 1))
        active_cells = [c for c in result if c.get("status") == "active"]
        assert len(active_cells) == 0

    def test_future_weekday_is_available(self):
        # Far future date — weekdays should be available
        today = date(2020, 1, 1)
        result = CalendarEngine.get_month_matrix(2024, 6, today=today)
        # June 2024 Monday (weekday=0) should be available (not a holiday/disabled)
        weekdays = [
            c for c in result if c.get("date") and c.get("weekday") in [0, 1, 2, 3, 4] and not c.get("is_holiday")
        ]
        available = [c for c in weekdays if c["status"] == "available"]
        assert len(available) > 0

    def test_cell_has_required_keys_for_real_days(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 4, 1))
        required_keys = {"num", "date", "status", "is_holiday", "weekday"}
        for cell in result:
            if cell["num"] != "":
                assert required_keys.issubset(cell.keys()), f"Missing keys in {cell}"

    def test_date_field_is_iso_format(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 4, 1))
        for cell in result:
            if cell.get("date"):
                # Should not raise
                parsed = date.fromisoformat(cell["date"])
                assert parsed.year == 2024
                assert parsed.month == 5

    def test_correct_number_of_real_days_for_may(self):
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 4, 1))
        real_days = [c for c in result if c["num"] != ""]
        assert len(real_days) == 31

    def test_correct_number_of_real_days_for_february_leap(self):
        result = CalendarEngine.get_month_matrix(2024, 2, today=date(2024, 1, 1))
        real_days = [c for c in result if c["num"] != ""]
        assert len(real_days) == 29  # 2024 is a leap year

    def test_holiday_flag_set_for_german_holidays(self):
        # May 1st 2024 is Tag der Arbeit (public holiday in Germany)
        today = date(2024, 4, 1)
        result = CalendarEngine.get_month_matrix(2024, 5, today=today, holidays_subdiv="ST")
        may_first = next((c for c in result if c.get("date") == "2024-05-01"), None)
        assert may_first is not None
        assert may_first["is_holiday"] is True

    def test_holiday_status_for_future_holiday(self):
        # May 1st 2024, it's a Wednesday (not Sunday), so should get "holiday" status
        today = date(2024, 4, 1)
        result = CalendarEngine.get_month_matrix(2024, 5, today=today)
        may_first = next((c for c in result if c.get("date") == "2024-05-01"), None)
        assert may_first is not None
        assert may_first["status"] == "holiday"

    def test_selected_date_overrides_other_status(self):
        # Select May 1st 2024 (a holiday) — it should show as 'active'
        today = date(2024, 4, 1)
        selected = date(2024, 5, 1)
        result = CalendarEngine.get_month_matrix(2024, 5, today=today, selected_date=selected)
        may_first = next((c for c in result if c.get("date") == "2024-05-01"), None)
        assert may_first is not None
        assert may_first["status"] == "active"

    def test_different_subdivision(self):
        # Test with BY (Bavaria) subdivision — should not error
        result = CalendarEngine.get_month_matrix(2024, 5, today=date(2024, 4, 1), holidays_subdiv="BY")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_today_is_available_not_disabled(self):
        # Today itself is NOT in the past, so it should be available (not disabled)
        today = date(2024, 6, 3)  # A Monday
        result = CalendarEngine.get_month_matrix(2024, 6, today=today)
        june_3 = next((c for c in result if c.get("date") == "2024-06-03"), None)
        assert june_3 is not None
        # today is NOT < today, so should not be disabled due to the past check
        # It could be "available", "holiday", or "active" but NOT "disabled"
        assert june_3["status"] != "disabled"


@pytest.mark.unit
class TestCalendarEngineGetMonthLabel:
    def test_january(self):
        label = CalendarEngine.get_month_label(2024, 1)
        assert "Январь" in label
        assert "2024" in label

    def test_december(self):
        label = CalendarEngine.get_month_label(2024, 12)
        assert "Декабрь" in label
        assert "2024" in label

    def test_all_months_have_names(self):
        for month_num in range(1, 13):
            label = CalendarEngine.get_month_label(2024, month_num)
            assert str(2024) in label
            assert len(label) > 4  # Should contain month name

    def test_may(self):
        label = CalendarEngine.get_month_label(2024, 5)
        assert "Май" in label

    def test_september(self):
        label = CalendarEngine.get_month_label(2023, 9)
        assert "Сентябрь" in label
        assert "2023" in label

    def test_format_contains_year(self):
        label = CalendarEngine.get_month_label(2025, 3)
        assert "2025" in label

    def test_unknown_month_returns_empty_name_with_year(self):
        # Month 0 or 13 would return empty name from the dict
        label = CalendarEngine.get_month_label(2024, 13)
        assert "2024" in label
        # Name part would be "" but year is appended

    def test_locale_parameter_accepted(self):
        # Default locale is "ru", but passing explicit "ru" should work
        label = CalendarEngine.get_month_label(2024, 6, locale="ru")
        assert "Июнь" in label
        assert "2024" in label
