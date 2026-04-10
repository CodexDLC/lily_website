"""Cabinet registration for booking module — navigation only.
Dashboard widgets live in system/cabinet.py (analytics module).
"""

from __future__ import annotations

from codex_django.cabinet import SidebarItem, TopbarEntry, declare
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

declare(
    module="booking",
    space="staff",
    settings_url="cabinet:booking_settings",
    topbar=TopbarEntry(
        group="services",
        label=str(_("Booking")),
        icon="bi-calendar-check",
        url=reverse_lazy("cabinet:booking_schedule"),
    ),
    sidebar=[
        SidebarItem(label=str(_("Schedule")), url=reverse_lazy("cabinet:booking_schedule"), icon="bi-calendar3"),
        SidebarItem(label=str(_("New booking")), url=reverse_lazy("cabinet:booking_new"), icon="bi-plus-circle"),
        SidebarItem(label=str(_("Appointments")), url=reverse_lazy("cabinet:booking_list"), icon="bi-list-ul"),
    ],
)


declare(
    module="staff",
    space="staff",
    topbar=TopbarEntry(
        group="admin",
        label=str(_("Staff")),
        icon="bi-person-vcard",
        url=reverse_lazy("cabinet:staff_list"),
        order=25,
    ),
    sidebar=[
        SidebarItem(
            label=str(_("Personnel")),
            url=reverse_lazy("cabinet:staff_list"),
            icon="bi-people",
        ),
    ],
)
