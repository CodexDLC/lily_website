from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from features.booking.models.master import Master
from features.booking.models.schedule import MasterWorkingDay

from src.lily_backend.cabinet.views.staff import MasterQuickEditForm


@pytest.mark.unit
class TestMasterQuickEditForm:
    def setup_method(self):
        self.factory = RequestFactory()
        self.master = MagicMock(spec=Master)
        self.master.work_days = [0, 1]  # Monday, Tuesday
        self.master.work_start = "09:00"
        self.master.work_end = "18:00"
        self.master.break_start = None
        self.master.break_end = None
        self.master.working_days = MagicMock()
        self.master.working_days.all.return_value = []

    def test_form_initial_data(self):
        """Test that form initializes with correct work_days from instance."""
        form = MasterQuickEditForm(instance=self.master)
        assert form.fields["work_days"].initial == ["0", "1"]

    @patch("src.lily_backend.cabinet.views.staff.BookingSettings")
    @patch("src.lily_backend.cabinet.views.staff.transaction.atomic")
    @patch("src.lily_backend.cabinet.views.staff.MasterWorkingDay.objects.update_or_create")
    def test_form_save_syncs_days(self, mock_update_or_create, mock_atomic, mock_booking_settings):
        """Test that saving the form triggers sync_working_days."""
        # Mock Context Manager
        mock_atomic.return_value.__enter__.return_value = None

        # Mock BookingSettings
        mock_settings = MagicMock()
        mock_settings.get_day_schedule.return_value = ("10:00", "19:00")
        mock_booking_settings.load.return_value = mock_settings

        data = {
            "name": "Test Master",
            "title": "Stylist",
            "status": "active",
            "order": 1,
            "is_public": True,
            "years_experience": 5,
            "work_days": ["0", "2"],  # Mo, We
        }

        form = MasterQuickEditForm(data=data, instance=self.master)
        assert form.is_valid(), form.errors

        # We need to mock instance.save to avoid DB
        with patch.object(self.master, "save"):
            form.save(commit=True)

        # Verify sync_working_days logic
        assert mock_update_or_create.call_count == 2  # Day 0 and Day 2

    @patch("src.lily_backend.cabinet.views.staff.BookingSettings")
    @patch("src.lily_backend.cabinet.views.staff.MasterWorkingDay.objects.update_or_create")
    def test_sync_working_days_deletes_removed_days(self, mock_update_or_create, mock_booking_settings):
        """Test that _sync_working_days deletes days that are no longer selected."""
        mock_day_0 = MagicMock(spec=MasterWorkingDay)
        mock_day_0.weekday = 0
        mock_day_1 = MagicMock(spec=MasterWorkingDay)
        mock_day_1.weekday = 1

        self.master.working_days.all.return_value = [mock_day_0, mock_day_1]

        # Mock BookingSettings
        mock_settings = MagicMock()
        mock_settings.get_day_schedule.return_value = ("09:00", "18:00")
        mock_booking_settings.load.return_value = mock_settings

        # Only day 0 is selected, so day 1 should be deleted
        MasterQuickEditForm._sync_working_days(self.master, [0])

        mock_day_1.delete.assert_called_once()
        mock_day_0.delete.assert_not_called()
        assert mock_update_or_create.call_count == 1
