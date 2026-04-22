import os
import sys
from datetime import date

import django

# Setup Django
sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from features.booking.booking_settings import BookingSettings  # noqa: E402
from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService  # noqa: E402


def verify_fix():
    print("Verifying booking fixes...")
    availability = CabinetBookingAvailabilityService()
    BookingSettings.load()

    # April 2026 has Sundays on 5, 12, 19, 26
    start_date = date(2026, 4, 1)
    horizon = 30
    service_ids = [5]  # Service 5 has no masters on Sundays

    print(f"Fetching availability for {start_date} with horizon {horizon} and service_ids {service_ids}...")
    try:
        results = availability.get_available_dates(start_date=start_date, horizon=horizon, service_ids=service_ids)
        print(f"Success! Found {len(results)} available dates.")
        print(f"Available dates: {sorted(list(results))}")

        # Verify Sundays are NOT in results but didn't cause crash
        sundays = ["2026-04-05", "2026-04-12", "2026-04-19", "2026-04-26"]
        for sunday in sundays:
            if sunday in results:
                print(f"!!! Error: Sunday {sunday} reached engine results erroneously.")
            else:
                print(f"Sunday {sunday} correctly handled (excluded).")

    except Exception as e:
        print(f"Verification failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    verify_fix()
