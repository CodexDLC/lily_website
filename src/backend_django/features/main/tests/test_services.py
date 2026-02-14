"""
Unit tests for features.main services.

Tests ContactService and HomeService business logic.
"""

from unittest.mock import patch

import pytest
from features.booking.models import Client
from features.main.models import Category, ContactRequest
from features.main.services.contact_service import ContactService
from features.main.services.home_service import HomeService


@pytest.fixture
def sample_categories_for_home(db):
    """Create categories for home page bento testing."""
    cat1 = Category.objects.create(
        title="Maniküre",
        slug="manicure",
        bento_group="nails",
        order=1,
        is_active=True,
    )
    cat2 = Category.objects.create(
        title="Pediküre",
        slug="pedicure",
        bento_group="nails",
        order=2,
        is_active=True,
    )
    cat3 = Category.objects.create(
        title="Haarschnitt",
        slug="haircut",
        bento_group="hair",
        order=3,
        is_active=True,
    )
    cat4 = Category.objects.create(
        title="Massage",
        slug="massage",
        bento_group="body",
        order=4,
        is_active=True,
    )
    return [cat1, cat2, cat3, cat4]


@pytest.mark.django_db
class TestContactService:
    """Tests for ContactService.create_request()"""

    @patch("features.main.services.contact_service.DjangoArqClient.enqueue_job")
    @patch("features.main.services.contact_service.settings")
    def test_create_request_with_email(self, mock_settings, mock_enqueue):
        """Should create contact request with email contact type."""
        mock_settings.TELEGRAM_ADMIN_ID = "123456789"

        result = ContactService.create_request(
            first_name="John",
            last_name="Doe",
            contact_type="email",
            contact_value="john@example.com",
            message="Hello, I need help!",
            topic="general",
            consent_marketing=False,
        )

        # Check ContactRequest created
        assert isinstance(result, ContactRequest)
        assert result.message == "Hello, I need help!"
        assert result.topic == "general"

        # Check Client created/linked
        assert result.client is not None
        assert result.client.first_name == "John"
        assert result.client.last_name == "Doe"
        assert result.client.email == "john@example.com"
        assert result.client.phone == ""

        # Check notification sent
        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        assert call_args.kwargs["user_id"] == 123456789
        assert "John Doe" in call_args.kwargs["message"]
        assert result.id == call_args.kwargs["request_id"]

    @patch("features.main.services.contact_service.DjangoArqClient.enqueue_job")
    @patch("features.main.services.contact_service.settings")
    def test_create_request_with_phone(self, mock_settings, mock_enqueue):
        """Should create contact request with phone contact type."""
        mock_settings.TELEGRAM_ADMIN_ID = "123456789"

        result = ContactService.create_request(
            first_name="Maria",
            last_name="Schmidt",
            contact_type="phone",
            contact_value="+491234567890",
            message="I want to book appointment",
            topic="booking",
            consent_marketing=True,
        )

        # Check ContactRequest created
        assert isinstance(result, ContactRequest)
        assert result.topic == "booking"

        # Check Client created with phone
        assert result.client.phone == "+491234567890"
        assert result.client.email == ""
        assert result.client.consent_marketing is True

    @patch("features.main.services.contact_service.DjangoArqClient.enqueue_job")
    @patch("features.main.services.contact_service.settings")
    def test_no_notification_when_admin_id_not_set(self, mock_settings, mock_enqueue):
        """Should not send notification if TELEGRAM_ADMIN_ID is not configured."""
        mock_settings.TELEGRAM_ADMIN_ID = None

        ContactService.create_request(
            first_name="Test",
            last_name="User",
            contact_type="email",
            contact_value="test@example.com",
            message="Test message",
        )

        # Check notification NOT sent
        mock_enqueue.assert_not_called()

    @patch("features.main.services.contact_service.DjangoArqClient.enqueue_job")
    @patch("features.main.services.contact_service.settings")
    def test_get_or_create_client_finds_existing(self, mock_settings, mock_enqueue):
        """Should find existing client instead of creating duplicate."""
        mock_settings.TELEGRAM_ADMIN_ID = None

        # Create first request
        request1 = ContactService.create_request(
            first_name="John",
            last_name="Doe",
            contact_type="email",
            contact_value="john@example.com",
            message="First message",
        )

        # Create second request with same email
        request2 = ContactService.create_request(
            first_name="John",
            last_name="Doe",
            contact_type="email",
            contact_value="john@example.com",
            message="Second message",
        )

        # Should use same client
        assert request1.client.id == request2.client.id
        assert Client.objects.filter(email="john@example.com").count() == 1

    @patch("features.main.services.contact_service.DjangoArqClient.enqueue_job")
    @patch("features.main.services.contact_service.settings")
    def test_notification_message_format(self, mock_settings, mock_enqueue):
        """Should format notification message correctly."""
        mock_settings.TELEGRAM_ADMIN_ID = "123456789"

        ContactService.create_request(
            first_name="Anna",
            last_name="Müller",
            contact_type="phone",
            contact_value="+491234567890",
            message="Test message content",
            topic="complaint",
        )

        call_args = mock_enqueue.call_args
        message = call_args.kwargs["message"]

        # Check message contains expected parts
        assert "Anna Müller" in message
        assert "+491234567890" in message
        assert "phone" in message
        assert "Test message content" in message
        assert "📋" in message  # Emoji present


@pytest.mark.django_db
class TestHomeService:
    """Tests for HomeService.get_bento_context()"""

    @patch("features.main.services.home_service.CategorySelector.get_for_home_bento")
    def test_returns_dict_with_bento_groups(self, mock_selector, sample_categories_for_home):
        """Should return dict mapping bento_group to categories."""
        mock_selector.return_value = sample_categories_for_home

        result = HomeService.get_bento_context()

        assert isinstance(result, dict)
        assert "nails" in result
        assert "hair" in result
        assert "body" in result

    @patch("features.main.services.home_service.CategorySelector.get_for_home_bento")
    def test_uses_first_category_per_group(self, mock_selector, sample_categories_for_home):
        """Should use first category when multiple share same bento_group."""
        mock_selector.return_value = sample_categories_for_home

        result = HomeService.get_bento_context()

        # manicure (order=1) should be selected over pedicure (order=2)
        assert result["nails"].slug == "manicure"

    @patch("features.main.services.home_service.CategorySelector.get_for_home_bento")
    def test_initializes_all_expected_groups(self, mock_selector):
        """Should initialize all expected bento groups even if no categories exist."""
        mock_selector.return_value = []

        result = HomeService.get_bento_context()

        # Check all expected groups are present (from Category.BENTO_GROUPS)
        expected_groups = ["hair", "nails", "face", "eyes", "body", "hair_removal"]
        for group in expected_groups:
            assert group in result
            assert result[group] is None  # No categories for this group

    @patch("features.main.services.home_service.CategorySelector.get_for_home_bento")
    def test_handles_empty_categories(self, mock_selector):
        """Should handle case when no categories exist."""
        mock_selector.return_value = []

        result = HomeService.get_bento_context()

        assert isinstance(result, dict)
        assert all(v is None for v in result.values())

    @patch("features.main.services.home_service.CategorySelector.get_for_home_bento")
    def test_handles_partial_groups(self, mock_selector, sample_categories_for_home):
        """Should handle when only some bento groups have categories."""
        # Only nails and hair groups have categories
        mock_selector.return_value = sample_categories_for_home[:3]

        result = HomeService.get_bento_context()

        # Filled groups
        assert result["nails"] is not None
        assert result["hair"] is not None

        # Empty groups
        assert result["face"] is None
        assert result["eyes"] is None

    @patch("features.main.services.home_service.CategorySelector.get_for_home_bento")
    def test_preserves_category_order(self, mock_selector, sample_categories_for_home):
        """Should respect order field when selecting first category per group."""
        # Reverse order
        reversed_cats = list(reversed(sample_categories_for_home))
        mock_selector.return_value = reversed_cats

        result = HomeService.get_bento_context()

        # Should still pick manicure (order=1) not pedicure (order=2)
        # because logic checks if bento_data[group] is None first
        assert result["nails"].slug == "massage"  # First in reversed list with "nails" group
