import os
import sys
import traceback
from datetime import date

import django

sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from features.booking.selector.engine import get_booking_engine_gateway  # noqa: E402


def capture_exception():
    gateway = get_booking_engine_gateway()
    target_date = date(2026, 4, 10)
    service_ids = [5]

    try:
        print(f"Calling get_available_slots for service {service_ids} on {target_date}...")
        result = gateway.get_available_slots(service_ids=service_ids, target_date=target_date)
        print(f"Result: {result}")
        if hasattr(result, "get_unique_start_times"):
            print(f"Times: {result.get_unique_start_times()}")
    except Exception:
        print("!!! CAUGHT EXCEPTION !!!")
        traceback.print_exc()


if __name__ == "__main__":
    capture_exception()
