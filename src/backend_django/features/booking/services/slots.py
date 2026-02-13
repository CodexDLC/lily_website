from datetime import date, datetime, time, timedelta

from django.utils import timezone
from features.booking.models import Appointment, Master
from features.system.models.site_settings import SiteSettings


class SlotService:
    """
    Service for calculating available time slots for booking.
    Optimized to maximize the number of appointments (no small gaps).
    """

    def __init__(self, step_minutes: int = 30):
        # step_minutes is used as a fallback or for grid alignment
        self.step_minutes = step_minutes

    def get_available_slots(self, masters: Master | list[Master], date_obj: date, duration_minutes: int) -> list[str]:
        if isinstance(masters, Master):
            masters = [masters]

        if not masters:
            return []

        all_slots = set()
        for master in masters:
            master_slots = self._get_slots_for_single_master(master, date_obj, duration_minutes)
            all_slots.update(master_slots)

        return sorted(list(all_slots))

    def _get_slots_for_single_master(self, master: Master, date_obj: date, duration_minutes: int) -> list[str]:
        """Calculates slots using 'tight packing' logic."""

        # 1. Get working hours
        working_hours = self._get_working_hours(date_obj)
        if not working_hours:
            return []

        start_work, end_work = working_hours

        # Helper to combine date and time into aware datetime
        def to_dt(t):
            return timezone.make_aware(datetime.combine(date_obj, t))

        # 2. Get busy intervals
        appointments = Appointment.objects.filter(
            master=master,
            datetime_start__date=date_obj,
            status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED],
        ).order_by("datetime_start")

        # Create a list of busy intervals [start, end] as datetimes
        busy_dts = []
        for app in appointments:
            s = timezone.localtime(app.datetime_start)
            e = s + timedelta(minutes=app.duration_minutes)
            busy_dts.append((s, e))

        # 3. Identify free windows (gaps)
        # We start from start_work and jump through busy intervals to end_work
        free_windows = []
        current_ptr = to_dt(start_work)
        end_limit = to_dt(end_work)

        for b_start, b_end in busy_dts:
            if b_start > current_ptr:
                free_windows.append((current_ptr, b_start))
            current_ptr = max(current_ptr, b_end)

        if current_ptr < end_limit:
            free_windows.append((current_ptr, end_limit))

        # 4. Generate slots for each window
        available_slots = []
        now = timezone.localtime()
        # Small technical buffer (15 min) to prevent booking in the past
        min_allowed_start = now + timedelta(minutes=15)

        service_delta = timedelta(minutes=duration_minutes)

        for w_start, w_end in free_windows:
            # A window must be at least as long as the service
            if (w_end - w_start) < service_delta:
                continue

            # Tight packing: offer slots starting from the beginning of the window
            # and also from the end of the window (backwards) to ensure no gaps.

            # Forward packing (from start of gap)
            temp_start = w_start
            while temp_start + service_delta <= w_end:
                if temp_start >= min_allowed_start:
                    available_slots.append(temp_start.strftime("%H:%M"))
                temp_start += service_delta  # Jump by duration to keep packing tight

            # Backward packing (from end of gap)
            # This ensures we offer the "final" possible slot in this window
            final_slot_start = w_end - service_delta
            if final_slot_start >= min_allowed_start and final_slot_start > w_start:
                available_slots.append(final_slot_start.strftime("%H:%M"))

        # Remove duplicates and sort
        return sorted(list(set(available_slots)))

    def _get_working_hours(self, date_obj: date) -> tuple[time, time] | None:
        settings = SiteSettings.load()
        weekday = date_obj.weekday()
        if weekday < 5:
            return settings.work_start_weekdays, settings.work_end_weekdays
        elif weekday == 5:
            return settings.work_start_saturday, settings.work_end_saturday
        else:
            return None
