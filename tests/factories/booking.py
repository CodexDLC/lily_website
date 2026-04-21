"""factory_boy factories for booking models."""

from __future__ import annotations

import datetime as _dt

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory
from tests.factories.main import ServiceCategoryFactory, ServiceFactory
from tests.factories.system import ClientFactory


class MasterFactory(DjangoModelFactory):
    class Meta:
        model = "booking.Master"
        django_get_or_create = ("slug",)
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Master {n}")
    slug = factory.Sequence(lambda n: f"master-{n}")
    status = "active"
    work_start = _dt.time(9, 0)
    work_end = _dt.time(18, 0)
    is_public = True

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for cat in extracted:
                self.categories.add(cat)
        else:
            self.categories.add(ServiceCategoryFactory())

    @factory.post_generation
    def working_days(self, create, extracted, **kwargs):
        """Create a full Mon–Sun working schedule by default."""
        if not create:
            return
        if extracted is False:
            return  # explicit opt-out: MasterFactory(working_days=False)
        from features.booking.models import MasterWorkingDay

        weekdays = extracted if extracted else range(7)
        for wd in weekdays:
            MasterWorkingDay.objects.get_or_create(
                master=self,
                weekday=wd,
                defaults={
                    "start_time": _dt.time(9, 0),
                    "end_time": _dt.time(18, 0),
                },
            )


class MasterWorkingDayFactory(DjangoModelFactory):
    class Meta:
        model = "booking.MasterWorkingDay"

    master = factory.SubFactory(MasterFactory, working_days=False)
    weekday = 0
    start_time = _dt.time(9, 0)
    end_time = _dt.time(18, 0)


class AppointmentFactory(DjangoModelFactory):
    class Meta:
        model = "booking.Appointment"

    client = factory.SubFactory(ClientFactory)
    master = factory.SubFactory(MasterFactory)
    service = factory.SubFactory(ServiceFactory)
    datetime_start = factory.LazyFunction(lambda: timezone.now() + _dt.timedelta(hours=48))
    duration_minutes = 60
    price = "50.00"
    status = "pending"


class AppointmentGroupFactory(DjangoModelFactory):
    class Meta:
        model = "booking.AppointmentGroup"

    client = factory.SubFactory(ClientFactory)
    status = "pending"


class AppointmentGroupItemFactory(DjangoModelFactory):
    class Meta:
        model = "booking.AppointmentGroupItem"

    group = factory.SubFactory(AppointmentGroupFactory)
    appointment = factory.SubFactory(AppointmentFactory)
    order = 0
