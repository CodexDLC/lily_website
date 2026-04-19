import os
import sys
from datetime import date

import django

sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from features.booking.selector.engine import get_booking_engine_gateway  # noqa: E402
from features.main.models.service import Service  # noqa: E402


def diag_adapter():
    gateway = get_booking_engine_gateway()
    target_date = date(2026, 4, 10)
    adapter = gateway._make_adapter(target_date=target_date)

    s_id = 5
    service_obj = Service.objects.get(id=s_id)
    weekday = target_date.weekday()

    print(f"Resolving masters for service {s_id} on weekday {weekday}...")
    masters = adapter._resolve_master_ids(service_obj, weekday, None, {}, s_id)
    print(f"Masters found: {masters}")


if __name__ == "__main__":
    diag_adapter()
