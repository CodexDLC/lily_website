import os
import sys

import django

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from features.booking.models import Appointment, Client  # noqa: E402

User = get_user_model()


def check_sync():
    print("--- Users ---")
    users = User.objects.all()
    for u in users:
        client_profile = getattr(u, "client_profile", None)
        print(f"User: {u.username} (ID: {u.id}), Client Profile: {client_profile}")

    print("\n--- Clients ---")
    clients = Client.objects.all()
    for c in clients:
        print(
            f"Client: {c.first_name} {c.last_name} (ID: {c.id}, Phone: {c.phone}, Email: {c.email}, Linked User: {c.user})"
        )

    print("\n--- Appointments for Mykhailo Abasov ---")
    appts = Appointment.objects.filter(client__first_name__icontains="Mykhailo")
    for a in appts:
        print(f"Appt ID: {a.id}, Client: {a.client}, Date: {a.datetime_start}")


if __name__ == "__main__":
    check_sync()
