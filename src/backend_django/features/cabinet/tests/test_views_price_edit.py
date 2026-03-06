from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from features.booking.models import Appointment
from features.booking.models.client import Client
from features.booking.models.master import Master
from features.main.models.category import Category
from features.main.models.service import Service

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def test_client():
    user = User.objects.create_user(username="client", email="client@example.com", password="pw")
    return Client.objects.create(user=user, phone="+1234567890", first_name="Test Client")


@pytest.fixture
def confirmed_appointment(test_client):
    cat = Category.objects.create(title="Category 1", is_active=True)
    svc = Service.objects.create(category=cat, title="Service 1", price=50.00, duration=60, is_active=True)
    master = Master.objects.create(
        user=User.objects.create_user(username="m", email="m@e.com", password="pw"), name="Master"
    )

    app = Appointment.objects.create(
        client=test_client,
        service=svc,
        master=master,
        datetime_start=timezone.now() + timedelta(days=1),
        duration_minutes=60,
        price=50.00,
        status=Appointment.STATUS_CONFIRMED,
    )
    return app


@pytest.fixture
def admin_client_user():
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="pw",  # pragma: allowlist secret
    )


def test_price_edit_view_access_denied_for_anonymous(client, confirmed_appointment):
    """Anonymous users should be redirected to login."""
    url = reverse("cabinet:edit_price", kwargs={"token": confirmed_appointment.finalize_token})
    response = client.get(url)
    assert response.status_code == 302
    # Expect redirect to standard login URL (accounts/login)
    assert "/accounts/login/" in response.url


def test_price_edit_view_access_denied_for_client(client, test_client, confirmed_appointment):
    """Clients (regular users) should get 403 Forbidden (AdminRequiredMixin)."""
    client.force_login(test_client.user)
    url = reverse("cabinet:edit_price", kwargs={"token": confirmed_appointment.finalize_token})
    response = client.get(url)
    # AdminRequiredMixin raises PermissionDenied (403) for non-staff users
    assert response.status_code == 403


def test_price_edit_view_access_granted_for_admin(client, admin_client_user, confirmed_appointment):
    """Admin users should see the price edit form."""
    client.force_login(admin_client_user)
    url = reverse("cabinet:edit_price", kwargs={"token": confirmed_appointment.finalize_token})
    response = client.get(url)
    assert response.status_code == 200
    assert "current_price" in response.context


def test_price_edit_view_updates_price(client, admin_client_user, confirmed_appointment):
    """Submitting the form should update price_actual but not change status."""
    client.force_login(admin_client_user)
    url = reverse("cabinet:edit_price", kwargs={"token": confirmed_appointment.finalize_token})

    assert confirmed_appointment.price_actual is None
    assert confirmed_appointment.status == Appointment.STATUS_CONFIRMED

    response = client.post(url, data={"price_actual": "75.50"})

    # Should redirect back or to success page
    assert response.status_code == 302

    confirmed_appointment.refresh_from_db()
    assert float(confirmed_appointment.price_actual or 0.0) == 75.50
    assert confirmed_appointment.status == Appointment.STATUS_CONFIRMED  # Status untouched
