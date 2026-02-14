"""
Unit tests for features.main models.

Tests Category, Service, ContactRequest, and PortfolioImage models.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from features.booking.models import Client
from features.main.models import Category, ContactRequest, PortfolioImage, Service


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for Category model."""

    def test_create_category(self):
        """Should create category with required fields."""
        category = Category.objects.create(
            title="Maniküre",
            slug="manicure",
            bento_group="nails",
            description="Professional nail care",
            order=1,
        )

        assert category.title == "Maniküre"
        assert category.slug == "manicure"
        assert category.bento_group == "nails"
        assert category.is_active is True  # Default value

    def test_str_representation(self):
        """Should return formatted string with title and bento group."""
        category = Category.objects.create(
            title="Haarschnitt",
            slug="haircut",
            bento_group="hair",
        )

        assert str(category) == "Haarschnitt (Friseur & Styling)"

    def test_get_absolute_url(self):
        """Should return correct detail URL."""
        category = Category.objects.create(
            title="Massage",
            slug="massage",
            bento_group="body",
        )

        url = category.get_absolute_url()
        assert url == "/massage/"  # Depends on your URL config

    def test_ordering(self):
        """Should order by order field, then title."""
        cat3 = Category.objects.create(title="C Category", slug="c", bento_group="hair", order=3)
        cat1 = Category.objects.create(title="A Category", slug="a", bento_group="nails", order=1)
        cat2 = Category.objects.create(title="B Category", slug="b", bento_group="face", order=1)

        categories = list(Category.objects.all())

        # order=1 comes first, then alphabetically by title
        assert categories[0] == cat2  # A Category (order=1, alphabetically first)
        assert categories[1] == cat1  # B Category (order=1, alphabetically second)
        assert categories[2] == cat3  # C Category (order=3)

    @patch("features.main.models.category.optimize_image")
    def test_save_optimizes_image(self, mock_optimize):
        """Should optimize image on save."""
        # Create mock image
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

        category = Category(
            title="Test",
            slug="test",
            bento_group="hair",
            image=image,
        )
        category.save()

        mock_optimize.assert_called_once()

    @patch("features.main.models.category.cache.delete_many")
    def test_save_invalidates_cache(self, mock_delete):
        """Should invalidate related caches on save."""
        Category.objects.create(
            title="Test",
            slug="test-cat",
            bento_group="nails",
        )

        # Should have called cache.delete_many
        mock_delete.assert_called()
        args = mock_delete.call_args[0][0]
        assert "active_categories_cache" in args
        assert "bento_grid_cache" in args
        assert "category_detail_test-cat" in args

    def test_bento_groups_choices(self):
        """Should have predefined bento group choices."""
        # Get choices
        bento_groups = dict(Category.BENTO_GROUPS)

        assert "hair" in bento_groups
        assert "nails" in bento_groups
        assert "face" in bento_groups
        assert "eyes" in bento_groups
        assert "body" in bento_groups
        assert "hair_removal" in bento_groups


@pytest.mark.django_db
class TestServiceModel:
    """Tests for Service model."""

    @pytest.fixture
    def sample_category(self):
        """Create sample category for service tests."""
        return Category.objects.create(
            title="Maniküre",
            slug="manicure",
            bento_group="nails",
        )

    def test_create_service(self, sample_category):
        """Should create service with required fields."""
        service = Service.objects.create(
            category=sample_category,
            title="Classic Manicure",
            slug="classic-manicure",
            price=Decimal("25.00"),
            duration=30,
            order=1,
        )

        assert service.title == "Classic Manicure"
        assert service.price == Decimal("25.00")
        assert service.duration == 30
        assert service.category == sample_category
        assert service.is_active is True

    def test_str_representation(self, sample_category):
        """Should return service title."""
        service = Service.objects.create(
            category=sample_category,
            title="Gel Manicure",
            slug="gel-manicure",
            price=Decimal("35.00"),
            duration=45,
        )

        assert str(service) == "Gel Manicure"

    def test_ordering(self, sample_category):
        """Should order by order field, then title."""
        svc3 = Service.objects.create(
            category=sample_category, title="C Service", slug="c", price=30, duration=30, order=3
        )
        svc1 = Service.objects.create(
            category=sample_category, title="A Service", slug="a", price=20, duration=20, order=1
        )
        svc2 = Service.objects.create(
            category=sample_category, title="B Service", slug="b", price=25, duration=25, order=1
        )

        services = list(Service.objects.all())

        assert services[0] == svc1
        assert services[1] == svc2
        assert services[2] == svc3

    def test_price_info_optional(self, sample_category):
        """Should allow custom price display text."""
        service = Service.objects.create(
            category=sample_category,
            title="Luxury Manicure",
            slug="luxury",
            price=Decimal("50.00"),
            duration=60,
            price_info="ab 50€",
        )

        assert service.price_info == "ab 50€"

    def test_duration_info_optional(self, sample_category):
        """Should allow custom duration display text."""
        service = Service.objects.create(
            category=sample_category,
            title="Express Manicure",
            slug="express",
            price=Decimal("20.00"),
            duration=15,
            duration_info="ca. 15-20 Min",
        )

        assert service.duration_info == "ca. 15-20 Min"

    def test_is_hit_default_false(self, sample_category):
        """Should default is_hit to False."""
        service = Service.objects.create(
            category=sample_category,
            title="Regular Service",
            slug="regular",
            price=Decimal("30.00"),
            duration=30,
        )

        assert service.is_hit is False

    @patch("features.main.models.service.optimize_image")
    def test_save_optimizes_image(self, mock_optimize, sample_category):
        """Should optimize image on save."""
        image = SimpleUploadedFile("service.jpg", b"content", content_type="image/jpeg")

        service = Service(
            category=sample_category,
            title="Test",
            slug="test",
            price=Decimal("20.00"),
            duration=30,
            image=image,
        )
        service.save()

        mock_optimize.assert_called_once()

    @patch("features.main.models.service.cache.delete_many")
    def test_save_invalidates_cache(self, mock_delete, sample_category):
        """Should invalidate related caches on save."""
        service = Service.objects.create(
            category=sample_category,
            title="Test Service",
            slug="test-svc",
            price=Decimal("25.00"),
            duration=30,
        )

        mock_delete.assert_called()
        args = mock_delete.call_args[0][0]
        assert "active_services_cache" in args
        assert "popular_services_cache" in args
        assert f"service_detail_{service.slug}" in args
        assert f"category_detail_{sample_category.slug}" in args


@pytest.mark.django_db
class TestPortfolioImageModel:
    """Tests for PortfolioImage model."""

    @pytest.fixture
    def sample_service(self, db):
        """Create sample service for portfolio tests."""
        category = Category.objects.create(title="Test Cat", slug="test-cat", bento_group="nails")
        return Service.objects.create(
            category=category,
            title="Test Service",
            slug="test-svc",
            price=Decimal("30.00"),
            duration=30,
        )

    def test_create_portfolio_image(self, sample_service):
        """Should create portfolio image."""
        image = SimpleUploadedFile("portfolio.jpg", b"content", content_type="image/jpeg")

        portfolio = PortfolioImage.objects.create(
            service=sample_service,
            image=image,
            title="Before/After",
            order=1,
        )

        assert portfolio.service == sample_service
        assert portfolio.title == "Before/After"
        assert portfolio.order == 1

    def test_str_representation(self, sample_service):
        """Should return formatted string with service title."""
        image = SimpleUploadedFile("img.jpg", b"content", content_type="image/jpeg")
        portfolio = PortfolioImage.objects.create(service=sample_service, image=image)

        assert str(portfolio) == "Image for Test Service"

    def test_ordering(self, sample_service):
        """Should order by order field, then created_at."""
        img1 = PortfolioImage.objects.create(
            service=sample_service,
            image=SimpleUploadedFile("1.jpg", b"c", content_type="image/jpeg"),
            order=2,
        )
        img2 = PortfolioImage.objects.create(
            service=sample_service,
            image=SimpleUploadedFile("2.jpg", b"c", content_type="image/jpeg"),
            order=1,
        )

        images = list(PortfolioImage.objects.all())

        assert images[0] == img2
        assert images[1] == img1

    @patch("features.main.models.service.optimize_image")
    def test_save_optimizes_image(self, mock_optimize, sample_service):
        """Should optimize image on save."""
        image = SimpleUploadedFile("portfolio.jpg", b"content", content_type="image/jpeg")

        portfolio = PortfolioImage(service=sample_service, image=image)
        portfolio.save()

        mock_optimize.assert_called_once()

    @patch("features.main.models.service.cache.delete_many")
    def test_save_invalidates_cache(self, mock_delete, sample_service):
        """Should invalidate related caches on save."""
        image = SimpleUploadedFile("img.jpg", b"content", content_type="image/jpeg")
        PortfolioImage.objects.create(service=sample_service, image=image)

        mock_delete.assert_called()


@pytest.mark.django_db
class TestContactRequestModel:
    """Tests for ContactRequest model."""

    @pytest.fixture
    def sample_client(self):
        """Create sample client for contact request tests."""
        return Client.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
        )

    def test_create_contact_request(self, sample_client):
        """Should create contact request with required fields."""
        request = ContactRequest.objects.create(
            client=sample_client,
            topic=ContactRequest.TOPIC_GENERAL,
            message="Test message",
        )

        assert request.client == sample_client
        assert request.topic == ContactRequest.TOPIC_GENERAL
        assert request.message == "Test message"
        assert request.is_processed is False

    def test_topic_choices(self):
        """Should have predefined topic choices."""
        choices_dict = dict(ContactRequest.TOPIC_CHOICES)

        assert ContactRequest.TOPIC_GENERAL in choices_dict
        assert ContactRequest.TOPIC_BOOKING in choices_dict
        assert ContactRequest.TOPIC_JOB in choices_dict
        assert ContactRequest.TOPIC_OTHER in choices_dict

    def test_default_topic(self, sample_client):
        """Should default to TOPIC_GENERAL."""
        request = ContactRequest.objects.create(
            client=sample_client,
            message="Test",
        )

        assert request.topic == ContactRequest.TOPIC_GENERAL

    def test_is_processed_default_false(self, sample_client):
        """Should default is_processed to False."""
        request = ContactRequest.objects.create(
            client=sample_client,
            message="Test",
        )

        assert request.is_processed is False

    def test_str_representation(self, sample_client):
        """Should return formatted string with ID and topic."""
        request = ContactRequest.objects.create(
            client=sample_client,
            topic=ContactRequest.TOPIC_BOOKING,
            message="Test",
        )

        result = str(request)
        assert f"Request #{request.pk}" in result
        assert "Booking Inquiry" in result

    def test_ordering(self, sample_client):
        """Should order by created_at descending (newest first)."""
        req1 = ContactRequest.objects.create(client=sample_client, message="First")
        req2 = ContactRequest.objects.create(client=sample_client, message="Second")

        requests = list(ContactRequest.objects.all())

        assert requests[0] == req2  # Newest first
        assert requests[1] == req1

    def test_admin_notes_optional(self, sample_client):
        """Should allow admin notes."""
        request = ContactRequest.objects.create(
            client=sample_client,
            message="Test",
            admin_notes="Called client back",
        )

        assert request.admin_notes == "Called client back"

    def test_get_topic_display(self, sample_client):
        """Should display human-readable topic."""
        request = ContactRequest.objects.create(
            client=sample_client,
            topic=ContactRequest.TOPIC_JOB,
            message="Test",
        )

        assert request.get_topic_display() == "Job / Career"
