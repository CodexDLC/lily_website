"""
Unit tests for main app models.
"""

import pytest
from features.main.models import Category, Service


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for Category model."""

    def test_create_category(self):
        """Should create category successfully."""
        category = Category.objects.create(
            title="Test Category",
            slug="test-category",
            bento_group="nails",
        )

        assert category.pk is not None
        assert category.title == "Test Category"
        assert category.slug == "test-category"
        assert category.is_active is True

    def test_str_representation(self):
        """Should return title and bento_group."""
        category = Category.objects.create(
            title="Manicure",
            slug="manicure",
            bento_group="nails",
        )

        result = str(category)
        assert "Manicure" in result


@pytest.mark.django_db
class TestServiceModel:
    """Tests for Service model."""

    def test_create_service(self):
        """Should create service successfully."""
        category = Category.objects.create(
            title="Nails",
            slug="nails-cat",
            bento_group="nails",
        )
        service = Service.objects.create(
            category=category,
            title="Gel Polish",
            slug="gel-polish",
            price=30.00,
            duration=45,
        )

        assert service.pk is not None
        assert service.title == "Gel Polish"
        assert service.price == 30.00
        assert service.is_active is True

    def test_str_representation(self):
        """Should return title."""
        category = Category.objects.create(
            title="Nails",
            slug="nails-cat2",
            bento_group="nails",
        )
        service = Service.objects.create(
            category=category,
            title="Manicure",
            slug="manicure-svc",
            price=25.00,
            duration=30,
        )

        assert "Manicure" in str(service)
