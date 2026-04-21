import pytest
from system.selectors.masters import MasterSelector
from tests.factories.booking import MasterFactory
from tests.factories.main import ServiceFactory


@pytest.mark.django_db
class TestMasterSelector:
    def test_get_masters_queryset(self):
        MasterFactory(name="B", order=2, slug="master-b")
        MasterFactory(name="A", order=1, slug="master-a")
        qs = MasterSelector.get_masters_queryset()
        assert qs.count() == 2
        assert qs[0].name == "A"
        assert qs[1].name == "B"

    def test_get_masters_grid_booking_ready(self):
        master = MasterFactory(status="active", is_public=True)
        ServiceFactory(is_active=True).masters.add(master)
        grid = MasterSelector.get_masters_grid()
        assert len(grid.items) == 1
        item = grid.items[0]
        assert item.badge == "Booking Ready"
        assert item.badge_style == "success"

    def test_get_masters_grid_vacation(self):
        MasterFactory(status="vacation")
        grid = MasterSelector.get_masters_grid()
        item = grid.items[0]
        assert item.badge_style == "warning"

    def test_get_masters_grid_no_services(self):
        MasterFactory(status="active")
        grid = MasterSelector.get_masters_grid()
        item = grid.items[0]
        assert item.badge != "Booking Ready"
        meta_labels = [m[1] for m in item.meta]
        assert any("No services linked for booking" in label for label in meta_labels)

    def test_get_masters_grid_no_schedule(self):
        master = MasterFactory(status="active", working_days=False)
        ServiceFactory(is_active=True).masters.add(master)
        grid = MasterSelector.get_masters_grid()
        item = grid.items[0]
        assert item.badge != "Booking Ready"
        meta_labels = [m[1] for m in item.meta]
        assert any("No working schedule for booking" in label for label in meta_labels)
