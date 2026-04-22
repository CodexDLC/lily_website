from unittest.mock import patch

import pytest
from cabinet.views.staff import MasterQuickEditForm
from django.utils import timezone
from features.booking.models import Master


@pytest.mark.django_db
class TestMasterQuickEditFormGaps:
    def test_form_initial_work_days(self, master):
        """Test that work_days initial values are correctly populated."""
        # master fixture already has 7 working days (0-6)
        form = MasterQuickEditForm(instance=master)
        assert set(form.fields["work_days"].initial) == {"0", "1", "2", "3", "4", "5", "6"}

    def test_save_sync_working_days_remove_and_add(self, master, booking_settings):
        """Test syncing working days: removing some and adding/updating others."""
        # Current: 0,1,2,3,4,5,6
        # Target: 0 (Mo), 2 (We)
        data = {
            "name": master.name,
            "status": master.status,
            "order": master.order,
            "years_experience": master.years_experience,
            "work_days": ["0", "2"],
        }
        form = MasterQuickEditForm(instance=master, data=data)
        assert form.is_valid(), form.errors

        with patch("features.booking.booking_settings.BookingSettings.load", return_value=booking_settings):
            form.save()

        # Verify days
        active_days = master.working_days.values_list("weekday", flat=True)
        assert set(active_days) == {0, 2}
        assert master.working_days.count() == 2

    def test_sync_working_days_fallback_to_settings(self, category, booking_settings):
        """Test syncing when master doesn't have work_start/end, falling back to settings."""
        master_no_times = Master.objects.create(
            name="No Times", slug="no-times", status=Master.STATUS_ACTIVE, work_start=None, work_end=None
        )
        master_no_times.categories.add(category)

        # We manually call _sync_working_days to test the logic
        with patch("features.booking.booking_settings.BookingSettings.load", return_value=booking_settings):
            MasterQuickEditForm._sync_working_days(master_no_times, [0])  # Monday

        wd = master_no_times.working_days.get(weekday=0)
        # Should take from booking_settings (09:00 - 18:00)
        assert wd.start_time == booking_settings.work_start_monday
        assert wd.end_time == booking_settings.work_end_monday

    def test_sync_working_days_preserve_existing_times(self, master, booking_settings):
        """Test that existing working day times are preserved if they exist."""
        wd_monday = master.working_days.get(weekday=0)
        wd_monday.start_time = timezone.datetime.strptime("11:00", "%H:%M").time()
        wd_monday.save()

        with patch("features.booking.booking_settings.BookingSettings.load", return_value=booking_settings):
            # Syncing Monday again
            MasterQuickEditForm._sync_working_days(master, [0])

        wd_monday.refresh_from_db()
        # Should still be 11:00, not reset to default 09:00
        assert wd_monday.start_time == timezone.datetime.strptime("11:00", "%H:%M").time()

    def test_sync_working_days_no_times_available(self, category, booking_settings):
        """Test that no MasterWorkingDay is created if no start/end time is available anywhere."""
        master_no_times = Master.objects.create(
            name="Empty",
            slug="empty",
            status=Master.STATUS_ACTIVE,
        )
        # Mock settings to return None for a day (e.g. Sunday is closed)
        with (
            patch.object(booking_settings, "get_day_schedule", return_value=(None, None)),
            patch("features.booking.booking_settings.BookingSettings.load", return_value=booking_settings),
        ):
            MasterQuickEditForm._sync_working_days(master_no_times, [6])  # Sunday

        assert master_no_times.working_days.count() == 0
