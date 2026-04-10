import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _

# Root of Django project: src/backend_django
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROJECT_NAME = os.environ.get("PROJECT_NAME", BASE_DIR.name)

UNFOLD = {
    "SITE_TITLE": os.environ.get("ADMIN_SITE_TITLE", f"{PROJECT_NAME.replace('_', ' ').title()} Admin"),
    "SITE_HEADER": os.environ.get("ADMIN_SITE_HEADER", PROJECT_NAME.replace("_", " ").title()),
    "SITE_SYMBOL": "spa",
    "COLORS": {
        "primary": {
            "50": "239, 246, 255",
            "100": "219, 234, 254",
            "200": "191, 219, 254",
            "300": "147, 197, 253",
            "400": "96, 165, 250",
            "500": "59, 130, 246",
            "600": "37, 99, 235",
            "700": "29, 78, 216",
            "800": "30, 64, 175",
            "900": "30, 58, 138",
            "950": "23, 37, 84",
        },
    },
    "COMMANDS": {
        "show": False,
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Salon Management"),
                "items": [
                    {
                        "title": _("Appointments"),
                        "icon": "event",
                        "link": "/admin/booking/appointment/",
                    },
                    {
                        "title": _("Groups"),
                        "icon": "collections_bookmark",
                        "link": "/admin/booking/appointmentgroup/",
                    },
                    {
                        "title": _("Masters"),
                        "icon": "person",
                        "link": "/admin/booking/master/",
                    },
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": "/admin/main/servicecategory/",
                    },
                    {
                        "title": _("Services"),
                        "icon": "content_cut",
                        "link": "/admin/main/service/",
                    },
                    {
                        "title": _("Combos"),
                        "icon": "redeem",
                        "link": "/admin/main/servicecombo/",
                    },
                    {
                        "title": _("Conflict Rules"),
                        "icon": "gavel",
                        "link": "/admin/main/serviceconflictrule/",
                    },
                    {
                        "title": _("Booking Settings"),
                        "icon": "settings",
                        "link": "/admin/booking/bookingsettings/",
                    },
                ],
            },
            {
                "title": _("Marketing & CRM"),
                "items": [
                    {
                        "title": _("Clients"),
                        "icon": "people",
                        "link": "/admin/system/client/",
                    },
                    {
                        "title": _("Conversations"),
                        "icon": "chat",
                        "link": "/admin/conversations/message/",
                    },
                ],
            },
            {
                "title": _("Analytics"),
                "items": [
                    {
                        "title": _("Page Views"),
                        "icon": "bar_chart",
                        "link": "/admin/tracking/pageview/",
                    },
                ],
            },
            {
                "title": _("System & Settings"),
                "items": [
                    {
                        "title": _("Site Settings"),
                        "icon": "settings",
                        "link": "/admin/system/sitesettings/",
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Static Translations"),
                        "icon": "translate",
                        "link": "/admin/system/statictranslation/",
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("SEO Pages"),
                        "icon": "search",
                        "link": "/admin/system/staticpageseo/",
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": "/admin/auth/user/",
                        "permission": lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
                "ru": "🇷🇺",
                "de": "🇩🇪",
                "uk": "🇺🇦",
            },
        },
    },
}
