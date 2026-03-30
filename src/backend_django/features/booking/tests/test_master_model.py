"""Tests for Master model methods and properties."""

import pytest
from features.booking.models.master import Master


@pytest.mark.unit
class TestMasterModelProperties:
    def test_is_available_for_booking_active(self, master):
        assert master.is_available_for_booking is True

    def test_is_available_for_booking_vacation(self, master):
        master.status = Master.STATUS_VACATION
        master.save()
        assert master.is_available_for_booking is False

    def test_is_available_for_booking_fired(self, master):
        master.status = Master.STATUS_FIRED
        master.save()
        assert master.is_available_for_booking is False

    def test_instagram_url_with_handle(self, master):
        master.instagram = "beauty_master"
        master.save()
        assert master.instagram_url == "https://instagram.com/beauty_master"

    def test_instagram_url_with_at_prefix(self, master):
        master.instagram = "@beauty_master"
        master.save()
        assert master.instagram_url == "https://instagram.com/beauty_master"

    def test_instagram_url_none_when_empty(self, master):
        master.instagram = ""
        master.save()
        assert master.instagram_url is None

    def test_bot_access_code_generated_on_save(self, master):
        assert master.bot_access_code is not None
        assert master.bot_access_code.startswith("LILY")
        assert len(master.bot_access_code) == 8

    def test_qr_token_generated_on_save(self, master):
        assert master.qr_token is not None
        assert len(master.qr_token) == 16

    def test_str_representation(self, master):
        assert str(master) == master.name


@pytest.mark.integration
class TestMasterServiceRelations:
    def test_can_perform_service_in_category(self, master, service):
        assert master.can_perform_service(service) is True

    def test_cannot_perform_service_wrong_category(self, master, service):
        from features.main.models.category import Category
        from features.main.models.service import Service

        other_cat = Category.objects.create(title="Hair", slug="hair-cat", bento_group="hair", is_active=True)
        other_service = Service.objects.create(
            category=other_cat, title="Haircut", slug="haircut", price="40.00", duration=45, is_active=True
        )
        assert master.can_perform_service(other_service) is False

    def test_get_available_services(self, master, service):
        result = master.get_available_services()
        assert service in result

    def test_get_available_services_excludes_inactive(self, master, category):
        from features.main.models.service import Service

        inactive = Service.objects.create(
            category=category, title="Inactive Svc", slug="inactive-svc", price="30.00", duration=30, is_active=False
        )
        result = master.get_available_services()
        assert inactive not in result
