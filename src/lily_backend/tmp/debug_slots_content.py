import os
import sys

import django

# Setup Django
sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from features.booking.services.cabinet_availability import CabinetBookingAvailabilityService  # noqa: E402


def debug_slots():
    availability = CabinetBookingAvailabilityService()

    # Case 1: Service 5, April 10 (Friday)
    service_ids = [5]
    target_date = "2026-04-10"

    print(f"Testing slots for service {service_ids} on {target_date}...")
    slots = availability.get_slots(booking_date=target_date, service_ids=service_ids)
    print(f"Slots found: {slots}")

    # Case 2: Empty service_ids
    print(f"Testing slots for empty service_ids on {target_date}...")
    slots_empty = availability.get_slots(booking_date=target_date, service_ids=[])
    print(f"Slots found (empty service_ids): {slots_empty}")


if __name__ == "__main__":
    debug_slots()
