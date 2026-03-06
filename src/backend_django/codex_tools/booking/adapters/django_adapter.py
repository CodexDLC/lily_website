"""
codex_tools.booking.adapters.django_adapter
=============================================
Universal adapter for Django.

Does NOT contain imports from specific project features.
Works with any models implementing the booking interface.
"""

from datetime import date, datetime, time, timedelta
from typing import Any

from codex_tools.booking.dto import (
    BookingEngineRequest,
    EngineResult,
    MasterAvailability,
    ServiceRequest,
)
from codex_tools.booking.modes import BookingMode
from codex_tools.booking.slot_calculator import SlotCalculator
from django.core.cache import cache
from django.utils import timezone


class DjangoAvailabilityAdapter:
    """
    Universal bridge between Django ORM and the booking engine.

    All models are passed upon initialization, making the adapter
    suitable for use in any project.
    """

    def __init__(
        self,
        master_model: type[Any],
        appointment_model: type[Any],
        service_model: type[Any],
        day_off_model: type[Any],
        booking_settings_model: type[Any],
        site_settings_model: type[Any],
        step_minutes: int = 30,
        appointment_status_filter: list[str] | None = None,
    ) -> None:
        """
        Args:
            master_model: Master model class.
            appointment_model: Appointment model class.
            service_model: Service model class.
            day_off_model: Day Off model class.
            booking_settings_model: Booking Settings model class.
            site_settings_model: Global Site Settings model class.
            step_minutes: Time grid step size.
            appointment_status_filter: List of statuses considered "busy".
                                       If None, the default ones (PENDING, CONFIRMED) are used.
        """
        self.master_model = master_model
        self.appointment_model = appointment_model
        self.service_model = service_model
        self.day_off_model = day_off_model
        self.booking_settings_model = booking_settings_model
        self.site_settings_model = site_settings_model

        self.step_minutes = step_minutes
        self._calc = SlotCalculator(step_minutes)

        # If the filter is not passed, try to guess (for backward compatibility)
        # But it is better to pass it explicitly.
        if appointment_status_filter:
            self.appointment_status_filter = appointment_status_filter
        else:
            # Fallback to defaults if model has these constants
            self.appointment_status_filter = [
                getattr(appointment_model, "STATUS_PENDING", "pending"),
                getattr(appointment_model, "STATUS_CONFIRMED", "confirmed"),
            ]
            # Optionally add RESCHEDULE_PROPOSED if it exists
            if hasattr(appointment_model, "STATUS_RESCHEDULE_PROPOSED"):
                self.appointment_status_filter.append(appointment_model.STATUS_RESCHEDULE_PROPOSED)

        # Cache settings inside the instance
        self._booking_settings = None
        self._site_settings = None

    def build_engine_request(
        self,
        service_ids: list[int],
        target_date: date,
        mode: BookingMode = BookingMode.SINGLE_DAY,
        locked_master_id: int | None = None,
        master_selections: dict[str, str] | None = None,
    ) -> BookingEngineRequest:
        """Builds an engine request using the passed models."""
        services = self.service_model.objects.filter(id__in=service_ids).select_related("category")
        service_map = {s.id: s for s in services}

        weekday = target_date.weekday()
        service_requests = []

        for idx, svc_id in enumerate(service_ids):
            service = service_map.get(svc_id)
            if not service:
                continue

            if locked_master_id:
                possible_ids = [str(locked_master_id)]
            elif master_selections and str(idx) in master_selections:
                m_id = master_selections[str(idx)]
                if m_id == "any":
                    masters = self.master_model.objects.filter(
                        categories=service.category, status=self.master_model.STATUS_ACTIVE
                    )
                    possible_ids = [str(m.pk) for m in masters if weekday in (m.work_days or [])]
                else:
                    possible_ids = [str(m_id)]
            else:
                masters = self.master_model.objects.filter(
                    categories=service.category,
                    status=self.master_model.STATUS_ACTIVE,
                )
                possible_ids = [str(m.pk) for m in masters if weekday in (m.work_days or [])]

            if not possible_ids:
                continue

            gap = getattr(service, "min_gap_after_minutes", 0) or 0

            service_requests.append(
                ServiceRequest(
                    service_id=str(svc_id),
                    duration_minutes=service.duration,
                    min_gap_after_minutes=gap,
                    possible_master_ids=possible_ids,
                )
            )

        return BookingEngineRequest(
            service_requests=service_requests,
            booking_date=target_date,
            mode=mode,
        )

    def build_masters_availability(
        self,
        master_ids: list[int],
        target_date: date,
        cache_ttl: int = 0,
        exclude_appointment_ids: list[int] | None = None,
    ) -> dict[str, MasterAvailability]:
        """
        Calculates availability using the passed models.

        Args:
            master_ids: List of master IDs.
            target_date: Target date.
            cache_ttl: Cache TTL.
            exclude_appointment_ids: List of appointment IDs to ignore
                                     (used when rescheduling).
        """
        cache_key = None
        if cache_ttl > 0 and not exclude_appointment_ids:
            sorted_ids = ",".join(str(i) for i in sorted(master_ids))
            cache_key = f"booking_avail:{target_date}:{sorted_ids}"
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

        settings = self._get_booking_settings()
        result: dict[str, MasterAvailability] = {}

        day_off_ids = set(
            self.day_off_model.objects.filter(master_id__in=master_ids, date=target_date).values_list(
                "master_id", flat=True
            )
        )

        # Filter appointments (using self.appointment_status_filter)
        appt_filter = {
            "master_id__in": master_ids,
            "datetime_start__date": target_date,
            "status__in": self.appointment_status_filter,
        }

        appointments_qs = self.appointment_model.objects.filter(**appt_filter)

        # Exclude appointments if needed (to accurately reschedule to the same time)
        if exclude_appointment_ids:
            appointments_qs = appointments_qs.exclude(id__in=exclude_appointment_ids)

        appointments = appointments_qs.order_by("datetime_start")

        busy_by_master: dict[int, list[tuple[datetime, datetime]]] = {mid: [] for mid in master_ids}
        for app in appointments:
            # Clear seconds and microseconds for clean calculations
            s = timezone.localtime(app.datetime_start).replace(second=0, microsecond=0)
            e = s + timedelta(minutes=app.duration_minutes)
            busy_by_master[app.master_id].append((s, e))

        masters = self.master_model.objects.filter(pk__in=master_ids)

        for master in masters:
            if master.pk in day_off_ids:
                continue

            working_hours = self._get_master_working_hours(master, target_date)
            if not working_hours:
                continue

            work_start_t, work_end_t = working_hours
            work_start_dt = timezone.make_aware(datetime.combine(target_date, work_start_t))
            work_end_dt = timezone.make_aware(datetime.combine(target_date, work_end_t))

            break_interval = self._get_break_interval(master, target_date)
            buffer = self._get_buffer_minutes(master, settings)

            free_windows = self._calc.merge_free_windows(
                work_start=work_start_dt,
                work_end=work_end_dt,
                busy_intervals=busy_by_master.get(master.pk, []),
                break_interval=break_interval,
                buffer_minutes=buffer,
                min_duration_minutes=self.step_minutes,  # Filter out useless garbage windows
            )

            result[str(master.pk)] = MasterAvailability(
                master_id=str(master.pk),
                free_windows=free_windows,
                buffer_between_minutes=buffer,
            )

        if cache_ttl > 0 and cache_key:
            cache.set(cache_key, result, timeout=cache_ttl)

        return result

    def lock_masters(self, master_ids: list[int]) -> None:
        """
        Locks master rows in the DB for atomic availability check.
        Must be called within transaction.atomic().
        Uses list() to force the execution of the query.
        """
        if not master_ids:
            return
        # Sorting IDs is important to prevent deadlocks
        sorted_ids = sorted(master_ids)
        list(self.master_model.objects.select_for_update().filter(pk__in=sorted_ids))

    def result_to_slots_map(self, result: EngineResult) -> dict[str, bool]:
        times = result.get_unique_start_times()
        return {t: True for t in times}

    # ---------------------------------------------------------------------------
    # Internal methods (use self.models)
    # ---------------------------------------------------------------------------

    def _get_master_working_hours(self, master, target_date: date) -> tuple[time, time] | None:
        """
        Determines the working hours of the master.
        Can be overridden in a subclass for custom logic.
        """
        weekday = target_date.weekday()
        if master.work_days and weekday not in master.work_days:
            return None

        individual_start = getattr(master, "work_start", None)
        individual_end = getattr(master, "work_end", None)

        if individual_start and individual_end:
            return individual_start, individual_end

        site = self._get_site_settings()
        if weekday < 5:
            return site.work_start_weekdays, site.work_end_weekdays
        elif weekday == 5:
            return site.work_start_saturday, site.work_end_saturday
        else:
            return None

    def _get_break_interval(self, master, target_date: date) -> tuple[datetime, datetime] | None:
        """
        Determines the master's break.
        Can be overridden in a subclass.
        """
        break_start = getattr(master, "break_start", None)
        break_end = getattr(master, "break_end", None)

        if break_start and break_end:
            bs = timezone.make_aware(datetime.combine(target_date, break_start))
            be = timezone.make_aware(datetime.combine(target_date, break_end))
            return bs, be

        return None

    def _get_buffer_minutes(self, master, settings) -> int:
        individual = getattr(master, "buffer_between_minutes", None)
        if individual is not None:
            return individual
        return settings.default_buffer_between_minutes

    def _get_booking_settings(self):
        if self._booking_settings is None:
            self._booking_settings = self.booking_settings_model.load()
        return self._booking_settings

    def _get_site_settings(self):
        if self._site_settings is None:
            self._site_settings = self.site_settings_model.load()
        return self._site_settings
