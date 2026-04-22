"""factory_boy factories for system models."""

from __future__ import annotations

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.local")


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = "system.UserProfile"

    user = factory.SubFactory(UserFactory)


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = "system.Client"

    user = factory.SubFactory(UserFactory)
    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = factory.Sequence(lambda n: f"Last{n}")
    phone = factory.Sequence(lambda n: f"+4911100{n:05d}")
    email = factory.Sequence(lambda n: f"client{n}@test.local")
    status = "guest"
