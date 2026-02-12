from datetime import date, datetime, time, timedelta

from django.utils import timezone
from features.booking.models import Appointment, Master
from features.system.models.site_settings import SiteSettings


class SlotService:
    """
    Service for calculating available time slots for booking.
    """

    def __init__(self, step_minutes: int = 30):
        self.step_minutes = step_minutes

    def get_available_slots(self, masters: Master | list[Master], date_obj: date, duration_minutes: int) -> list[str]:
        """
        Returns a list of available start times (e.g. ["10:00", "10:30"])
        for given master(s), date, and service duration.

        If multiple masters are provided (e.g. 'Any Master'), returns the UNION of their slots.
        """
        if isinstance(masters, Master):
            masters = [masters]

        if not masters:
            return []

        # Set of all unique available slots across all masters
        all_slots = set()

        for master in masters:
            master_slots = self._get_slots_for_single_master(master, date_obj, duration_minutes)
            all_slots.update(master_slots)

        # Return sorted list
        return sorted(list(all_slots))

    def _get_slots_for_single_master(self, master: Master, date_obj: date, duration_minutes: int) -> list[str]:
        """Calculates slots for one specific master."""

        # 1. Get working hours for this day
        working_hours = self._get_working_hours(date_obj)
        if not working_hours:
            return []  # Day off

        start_work, end_work = working_hours

        # 2. Get existing appointments
        appointments = Appointment.objects.filter(
            master=master,
            datetime_start__date=date_obj,
            status__in=[Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED],
        ).order_by("datetime_start")

        busy_intervals = []
        for app in appointments:
            start = app.datetime_start.time()
            # Calculate end time based on duration
            end_dt = app.datetime_start + timedelta(minutes=app.duration_minutes)
            end = end_dt.time()
            busy_intervals.append((start, end))

        # 3. Generate slots
        available_slots = []
        current_time = start_work

        # Convert duration to timedelta
        service_delta = timedelta(minutes=duration_minutes)

        # Helper to combine date and time
        def to_dt(t):
            return datetime.combine(date_obj, t)

        while current_time < end_work:
            slot_start = current_time
            # Calculate when this service would end
            slot_end_dt = to_dt(slot_start) + service_delta
            slot_end = slot_end_dt.time()

            # Check if slot fits in working hours
            if slot_end > end_work and slot_end_dt.date() == date_obj:
                # If it goes past end_work on the same day
                break
            if slot_end_dt.date() > date_obj:
                # If it goes to next day (should not happen usually)
                break

            # Check collisions
            is_busy = False
            for busy_start, busy_end in busy_intervals:
                # Overlap logic:
                # (StartA < EndB) and (EndA > StartB)
                if slot_start < busy_end and slot_end > busy_start:
                    is_busy = True
                    break

            # Check if slot is in the past (for today)
            now = timezone.now()
            if date_obj == now.date():
                # Add a small buffer (e.g. 15 minutes) so user can't book immediately
                min_booking_time = now + timedelta(minutes=15)
                if to_dt(slot_start) < min_booking_time:
                    is_busy = True

            if not is_busy:
                available_slots.append(slot_start.strftime("%H:%M"))

            # Increment time
            next_dt = to_dt(current_time) + timedelta(minutes=self.step_minutes)
            current_time = next_dt.time()

        return available_slots

    def _get_working_hours(self, date_obj: date) -> tuple[time, time] | None:
        """
        Parses working hours from SiteSettings based on weekday.
        Returns (start_time, end_time) or None if closed.
        """
        settings = SiteSettings.load()
        weekday = date_obj.weekday()  # 0=Mon, 6=Sun

        if weekday < 5:  # Mon-Fri
            return settings.work_start_weekdays, settings.work_end_weekdays
        elif weekday == 5:  # Sat
            return settings.work_start_saturday, settings.work_end_saturday
        else:  # Sun
            return None  # Closed
