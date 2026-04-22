import os
import sys

import django
from django.template.loader import render_to_string
from django.test import RequestFactory

sys.path.append("c:\\install\\projects\\clients\\lily_website\\src\\lily_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()


def check_html_size():
    factory = RequestFactory()
    request = factory.get("/")
    context = {"slots": [], "date": "2026-04-10", "service_id": 5, "request": request}
    html = render_to_string("features/booking/partials/slots_panel.html", context)
    print(f"HTML Length (empty slots): {len(html)}")
    print("--- HTML ---")
    print(html)
    print("------------")


if __name__ == "__main__":
    check_html_size()
