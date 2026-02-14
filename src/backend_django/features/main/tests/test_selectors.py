"""
Unit tests for features.main selectors.

Tests CategorySelector methods with proper database setup and cache handling.
"""

import pytest
from django.core.cache import cache
from features.booking.models import Master
from features.main.models import Category, Service
from features.main.selectors.categories import CategorySelector


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before and after each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def sample_categories(db):
    """Create sample categories for testing."""
    cat1 = Category.objects.create(
        title="Maniküre",
        slug="manicure",
        bento_group="nails",
        description="Professional nail care",
        order=1,
        is_active=True,
    )
    cat2 = Category.objects.create(
        title="Pediküre",
        slug="pedicure",
        bento_group="nails",
        description="Foot care services",
        order=2,
        is_active=True,
    )
    cat3 = Category.objects.create(
        title="Haarschnitt",
        slug="haircut",
        bento_group="hair",
        description="Hair cutting services",
        order=3,
        is_active=True,
    )
    # Inactive category
    cat4 = Category.objects.create(
        title="Inactive Service",
        slug="inactive",
        bento_group="hair",
        description="Not shown",
        order=99,
        is_active=False,
    )
    return [cat1, cat2, cat3, cat4]


@pytest.fixture
def sample_services(db, sample_categories):
    """Create sample services for testing."""
    cat1 = sample_categories[0]
    service1 = Service.objects.create(
        category=cat1,
        title="Classic Manicure",
        duration=30,
        price=25.00,
        order=1,
        is_active=True,
    )
    service2 = Service.objects.create(
        category=cat1,
        title="Gel Manicure",
        duration=45,
        price=35.00,
        order=2,
        is_active=True,
    )
    # Inactive service
    service3 = Service.objects.create(
        category=cat1,
        title="Inactive Service",
        duration=60,
        price=50.00,
        order=99,
        is_active=False,
    )
    return [service1, service2, service3]


@pytest.fixture
def sample_masters(db, sample_categories):
    """Create sample masters for testing."""
    cat1 = sample_categories[0]
    master1 = Master.objects.create(
        name="Anna Schmidt",
        status="active",
        order=1,
    )
    master1.categories.add(cat1)

    master2 = Master.objects.create(
        name="Maria Müller",
        status="inactive",
        order=2,
    )
    master2.categories.add(cat1)

    return [master1, master2]


@pytest.mark.django_db
class TestCategorySelectorGetBentoGroups:
    """Tests for CategorySelector.get_bento_groups()"""

    def test_returns_dict_with_bento_groups(self, sample_categories):
        """Should return dict mapping bento_group to category."""
        result = CategorySelector.get_bento_groups()

        assert isinstance(result, dict)
        assert "nails" in result
        assert "hair" in result
        assert result["nails"].slug == "manicure"  # First by order
        assert result["hair"].slug == "haircut"

    def test_excludes_inactive_categories(self, sample_categories):
        """Should not include inactive categories."""
        result = CategorySelector.get_bento_groups()

        # Ensure inactive category is not in results
        assert all(cat.is_active for cat in result.values())

    def test_uses_cache(self, sample_categories):
        """Should cache results on second call."""
        # First call
        CategorySelector.get_bento_groups()

        # Modify DB
        Category.objects.filter(slug="manicure").update(title="Modified")

        # Second call should return cached data
        result2 = CategorySelector.get_bento_groups()

        assert result2["nails"].title == "Maniküre"  # Not "Modified"

    def test_returns_first_category_when_multiple_same_group(self, sample_categories):
        """Should return first category by order when multiple share bento_group."""
        result = CategorySelector.get_bento_groups()

        # Both manicure and pedicure have bento_group="nails"
        # Should return manicure (order=1)
        assert result["nails"].slug == "manicure"


@pytest.mark.django_db
class TestCategorySelectorGetForHomeBento:
    """Tests for CategorySelector.get_for_home_bento()"""

    def test_returns_list_of_active_categories(self, sample_categories):
        """Should return list of active categories ordered by order field."""
        result = CategorySelector.get_for_home_bento()

        assert isinstance(result, list)
        assert len(result) == 3  # 3 active categories
        assert result[0].slug == "manicure"
        assert result[1].slug == "pedicure"
        assert result[2].slug == "haircut"

    def test_excludes_inactive_categories(self, sample_categories):
        """Should not include inactive categories."""
        result = CategorySelector.get_for_home_bento()

        assert all(cat.is_active for cat in result)
        assert not any(cat.slug == "inactive" for cat in result)

    def test_only_loads_required_fields(self, sample_categories):
        """Should use only() to optimize query."""
        result = CategorySelector.get_for_home_bento()

        # Just verify it returns data (actual optimization check requires query logging)
        assert result[0].title
        assert result[0].slug
        assert result[0].bento_group

    def test_uses_cache(self, sample_categories):
        """Should cache results."""
        CategorySelector.get_for_home_bento()

        # Modify DB
        Category.objects.filter(slug="manicure").update(title="Modified")

        # Second call should return cached data
        result2 = CategorySelector.get_for_home_bento()

        assert result2[0].title == "Maniküre"


@pytest.mark.django_db
class TestCategorySelectorGetForPriceList:
    """Tests for CategorySelector.get_for_price_list()"""

    def test_returns_categories_with_services(self, sample_categories, sample_services):
        """Should return categories with prefetched services."""
        result = CategorySelector.get_for_price_list()

        assert len(result) == 3  # 3 active categories
        # Check services are prefetched
        cat = result[0]  # manicure
        services = list(cat.services.all())
        assert len(services) == 2  # 2 active services

    def test_filters_by_bento_group(self, sample_categories, sample_services):
        """Should filter categories by bento_group when provided."""
        result = CategorySelector.get_for_price_list(bento_group="nails")

        assert len(result) == 2  # manicure + pedicure
        assert all(cat.bento_group == "nails" for cat in result)

    def test_excludes_inactive_services(self, sample_categories, sample_services):
        """Should only include active services."""
        result = CategorySelector.get_for_price_list()

        cat = result[0]
        services = list(cat.services.all())
        assert all(svc.is_active for svc in services)
        assert not any(svc.title == "Inactive Service" for svc in services)

    def test_services_ordered_correctly(self, sample_categories, sample_services):
        """Should order services by order field, then title."""
        result = CategorySelector.get_for_price_list()

        cat = result[0]
        services = list(cat.services.all())
        assert services[0].title == "Classic Manicure"
        assert services[1].title == "Gel Manicure"

    def test_uses_cache_with_bento_group(self, sample_categories, sample_services):
        """Should cache results per bento_group."""
        CategorySelector.get_for_price_list(bento_group="nails")

        # Modify DB
        Category.objects.filter(slug="manicure").update(title="Modified")

        # Second call should return cached data
        result2 = CategorySelector.get_for_price_list(bento_group="nails")

        assert result2[0].title == "Maniküre"


@pytest.mark.django_db
class TestCategorySelectorGetDetail:
    """Tests for CategorySelector.get_detail()"""

    def test_returns_category_by_slug(self, sample_categories, sample_services, sample_masters):
        """Should return category with prefetched services and masters."""
        result = CategorySelector.get_detail("manicure")

        assert result is not None
        assert result.slug == "manicure"

        # Check services prefetched
        services = list(result.services.all())
        assert len(services) == 2

        # Check masters prefetched
        masters = list(result.masters.all())
        assert len(masters) == 1  # Only active master

    def test_returns_none_for_nonexistent_slug(self):
        """Should return None if category doesn't exist."""
        result = CategorySelector.get_detail("nonexistent")

        assert result is None

    def test_returns_none_for_inactive_category(self, sample_categories):
        """Should return None for inactive categories."""
        result = CategorySelector.get_detail("inactive")

        assert result is None

    def test_only_includes_active_services(self, sample_categories, sample_services):
        """Should only prefetch active services."""
        result = CategorySelector.get_detail("manicure")

        services = list(result.services.all())
        assert all(svc.is_active for svc in services)

    def test_only_includes_active_masters(self, sample_categories, sample_masters):
        """Should only prefetch active masters."""
        result = CategorySelector.get_detail("manicure")

        masters = list(result.masters.all())
        assert all(m.status == "active" for m in masters)

    def test_uses_cache(self, sample_categories, sample_services):
        """Should cache results per slug."""
        CategorySelector.get_detail("manicure")

        # Modify DB
        Category.objects.filter(slug="manicure").update(title="Modified")

        # Second call should return cached data
        result2 = CategorySelector.get_detail("manicure")

        assert result2.title == "Maniküre"
