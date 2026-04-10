import os
import sys

import django

# Setup Django
sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from features.booking.models import Master  # noqa: E402
from features.main.models import Service  # noqa: E402


def check_availability():
    print("Checking active services...")
    services = Service.objects.filter(is_active=True).prefetch_related("masters")
    for s in services:
        if s.id != 5:
            continue  # Focus on service 5
        masters = s.masters.filter(status=Master.STATUS_ACTIVE)
        print(f"Service: ID={s.id}, Name={s.name}")

        for weekday in range(7):
            # Simulate _resolve_master_ids logic
            working_masters = masters.filter(working_days__weekday=weekday)
            print(f"  Weekday {weekday}: {working_masters.count()} masters available")
            if working_masters.count() == 0:
                print(f"    !!! Sunday/DayOff? No masters on weekday {weekday} !!!")


if __name__ == "__main__":
    check_availability()


if __name__ == "__main__":
    check_availability()
