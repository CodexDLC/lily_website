"""factory_boy factories for features.main models."""

from __future__ import annotations

import factory
from factory.django import DjangoModelFactory


class ServiceCategoryFactory(DjangoModelFactory):
    class Meta:
        model = "main.ServiceCategory"
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")
    bento_group = "nails"
    is_planned = False


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = "main.Service"
        django_get_or_create = ("slug",)

    category = factory.SubFactory(ServiceCategoryFactory)
    name = factory.Sequence(lambda n: f"Service {n}")
    slug = factory.Sequence(lambda n: f"service-{n}")
    price = "50.00"
    duration = 60
    is_active = True
