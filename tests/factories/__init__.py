"""
factory_boy factories for Django ORM models.

Usage in tests:

    from tests.factories import MasterFactory, ClientFactory, AppointmentFactory

    def test_something(db):
        master = MasterFactory()
        appt = AppointmentFactory(master=master, status="confirmed")
"""

from tests.factories.booking import (
    AppointmentFactory,
    MasterFactory,
    MasterWorkingDayFactory,
)
from tests.factories.main import ServiceCategoryFactory, ServiceFactory
from tests.factories.system import ClientFactory

__all__ = [
    "AppointmentFactory",
    "ClientFactory",
    "MasterFactory",
    "MasterWorkingDayFactory",
    "ServiceCategoryFactory",
    "ServiceFactory",
]
