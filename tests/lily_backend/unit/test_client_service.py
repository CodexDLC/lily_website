from decimal import Decimal

import pytest
from cabinet.services.client import ClientService
from django.utils import timezone
from tests.factories.booking import AppointmentFactory
from tests.factories.system import ClientFactory, UserFactory, UserProfileFactory


@pytest.mark.django_db
class TestClientService:
    def test_get_corner_context_with_client(self, rf):
        user = UserFactory()
        client = ClientFactory(user=user, first_name="John", last_name="Doe")
        UserProfileFactory(user=user)
        AppointmentFactory(client=client, status="completed", price=Decimal("100.00"))
        request = rf.get("/")
        request.user = user
        context = ClientService.get_corner_context(request)
        assert context["corner_summary"]["display_name"] == "John Doe"
        assert context["corner_summary"]["stats"][0].value == "1"
        assert context["corner_summary"]["stats"][1].value == "€100"

    def test_get_corner_context_no_client_only_profile(self, rf):
        user = UserFactory()
        UserProfileFactory(user=user, first_name="Jane", last_name="Smith")
        request = rf.get("/")
        request.user = user
        context = ClientService.get_corner_context(request)
        assert context["corner_summary"]["display_name"] == "Jane Smith"
        assert context["corner_summary"]["stats"][0].value == "0"
        assert context["corner_summary"]["stats"][1].value == "€0"

    def test_get_appointments_context(self, rf):
        user = UserFactory()
        client = ClientFactory(user=user)
        AppointmentFactory(
            client=client, status="confirmed", datetime_start=timezone.now() + timezone.timedelta(days=1)
        )
        AppointmentFactory(
            client=client, status="completed", datetime_start=timezone.now() - timezone.timedelta(days=1)
        )
        request = rf.get("/")
        request.user = user
        context = ClientService.get_appointments_context(request)
        assert context["appointments_stats"][0].value == "1"
        assert context["appointments_stats"][1].value == "1"
        assert context["history_total_count"] == 1
        assert len(context["upcoming_table"].rows) == 1

    def test_save_corner_profile(self, rf):
        user = UserFactory()
        client = ClientFactory(user=user, first_name="OldFirst")
        profile = UserProfileFactory(user=user, instagram="old_insta")
        request = rf.post(
            "/",
            {
                "first_name": "NewFirst",
                "last_name": "NewLast",
                "phone": "+9999",
                "email": "new@test.local",
                "instagram": "new_insta",
                "notify_service": "on",
            },
        )
        request.user = user
        success, msg = ClientService.save_corner_profile(request)
        assert success is True
        client.refresh_from_db()
        profile.refresh_from_db()
        assert client.first_name == "NewFirst"
        assert profile.instagram == "new_insta"
        assert profile.notify_service is True
