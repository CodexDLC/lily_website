import os
import sys
from datetime import date

import django

sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from features.booking.models.schedule import MasterWorkingDay  # noqa: E402


def diag():
    target_date = date(2026, 4, 10)  # Friday
    weekday = target_date.weekday()
    service_ids = [5]

    print(f"Target date: {target_date}, weekday: {weekday}")

    qs = MasterWorkingDay.objects.filter(
        weekday=weekday,
        master__services__id__in=service_ids,
        master__status="active",
    )
    print(f"Query: {qs.query}")
    print(f"Count: {qs.count()}")
    for mw in qs:
        print(f"Found Master: {mw.master.id} {mw.master.name}")


if __name__ == "__main__":
    diag()
