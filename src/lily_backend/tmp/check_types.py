import os
import sys

import django

sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from codex_django.booking.selectors import get_available_slots  # noqa: E402

print(f"runtime_get_available_slots: {get_available_slots}")

# Check what happens with empty services
try:
    from codex_django.booking import DjangoAvailabilityAdapter

    class DummyAdapter(DjangoAvailabilityAdapter):
        def _resolve_master_ids(self, *args, **kwargs):
            return []

    # result = get_available_slots(DummyAdapter(), [5], '2026-04-12') # This would fail
except Exception as e:
    print(f"Error during dummy call: {e}")
