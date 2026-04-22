from unittest.mock import MagicMock, patch

import pytest
from codex_django.cabinet.registry import cabinet_registry
from features.main.cabinet import get_catalog_sidebar, refresh_catalog_categories, register_catalog_shell


@pytest.fixture
def isolated_cabinet_registry():
    topbar_entries = {group: list(entries) for group, entries in cabinet_registry._topbar_entries.items()}
    sidebar = dict(cabinet_registry._sidebar)
    module_topbar = dict(cabinet_registry._module_topbar)
    module_spaces = {module: set(spaces) for module, spaces in cabinet_registry._module_spaces.items()}

    yield

    cabinet_registry._topbar_entries = topbar_entries
    cabinet_registry._sidebar = sidebar
    cabinet_registry._module_topbar = module_topbar
    cabinet_registry._module_spaces = module_spaces


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

    def test_catalog_shell_registration_is_idempotent(self, mock_service_category, isolated_cabinet_registry):
        mock_service_category.objects.all().order_by.return_value = []

        register_catalog_shell()
        register_catalog_shell()
        refresh_catalog_categories()
        refresh_catalog_categories()

        admin_entries = cabinet_registry._topbar_entries["admin"]
        catalog_entries = [entry for entry in admin_entries if str(entry.label) == "Catalog"]

        assert len(catalog_entries) == 1
        assert len(cabinet_registry.get_sidebar("staff", "catalog")) == 1
