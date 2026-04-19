"""factory_boy factories for system models."""

from __future__ import annotations

import factory
from factory.django import DjangoModelFactory


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = "system.Client"

    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = factory.Sequence(lambda n: f"Last{n}")
    phone = factory.Sequence(lambda n: f"+4911100{n:05d}")
    email = factory.Sequence(lambda n: f"client{n}@test.local")
    status = "guest"
