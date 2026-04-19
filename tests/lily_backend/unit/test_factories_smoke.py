"""Smoke test that tests.factories resolve Django models and build valid rows."""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_factories_build_full_booking_graph(db, booking_settings):
    from tests.factories import (
        AppointmentFactory,
        ClientFactory,
        MasterFactory,
        ServiceFactory,
    )

    master = MasterFactory()
    service = ServiceFactory()
    client = ClientFactory()
    appt = AppointmentFactory(master=master, service=service, client=client)

    assert master.pk is not None
    assert service.pk is not None
    assert client.pk is not None
    assert appt.pk is not None
    assert appt.master_id == master.pk
    assert list(master.working_days.values_list("weekday", flat=True)) == [0, 1, 2, 3, 4, 5, 6]


@pytest.mark.unit
def test_master_factory_opts_out_of_working_days(db):
    from tests.factories import MasterFactory

    master = MasterFactory(working_days=False)
    assert master.working_days.count() == 0
