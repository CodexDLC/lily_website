from unittest.mock import MagicMock, patch

import pytest
from features.main.cabinet import get_catalog_sidebar


class TestMainCabinet:
    @pytest.fixture
    def mock_service_category(self):
        with patch("features.main.cabinet.ServiceCategory") as mock:
            yield mock

    def test_get_catalog_sidebar_empty(self, mock_service_category):
        mock_service_category.objects.all().order_by.return_value = []

        items = get_catalog_sidebar()

        # Should always have "All Services"
        assert len(items) == 1
        assert items[0].label == "All Services"
        assert items[0].order == 1

    def test_get_catalog_sidebar_dynamic(self, mock_service_category):
        cat1 = MagicMock(name="Cat 1", slug="cat-1")
        cat1.name = "Category 1"
        cat1.slug = "cat-1"

        cat2 = MagicMock(name="Cat 2", slug="cat-2")
        cat2.name = "Category 2"
        cat2.slug = "cat-2"

        mock_service_category.objects.all().order_by.return_value = [cat1, cat2]

        items = get_catalog_sidebar()

        # 1 (All) + 2 (Cats) = 3
        assert len(items) == 3
        assert items[1].label == "Category 1"
        assert items[1].order == 2
        assert items[2].label == "Category 2"
        assert items[2].order == 3

    def test_get_catalog_sidebar_operational_error(self, mock_service_category):
        from django.db import OperationalError

        mock_service_category.objects.all().side_effect = OperationalError("Table not found")

        # Should not crash, just return default
        items = get_catalog_sidebar()
        assert len(items) == 1
        assert items[0].label == "All Services"
