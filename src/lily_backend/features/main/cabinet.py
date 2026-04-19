import sys

from codex_django.cabinet import (
    SidebarItem,
    TopbarEntry,
    declare,
)
from core.logger import logger
from django.db import OperationalError
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from features.main.models import ServiceCategory


def get_catalog_sidebar() -> list[SidebarItem]:
    """Dynamically generate sidebar items for each service category."""
    items = [
        SidebarItem(
            label=str(_("All Services")),
            url=reverse_lazy("cabinet:services_list"),
            icon="bi-grid",
            order=1,
        )
    ]

    try:
        categories = ServiceCategory.objects.all().order_by("order", "name")
        for i, category in enumerate(categories, start=2):
            items.append(
                SidebarItem(
                    label=category.name,
                    url=reverse_lazy("cabinet:services_category", kwargs={"category_slug": category.slug}),
                    icon="bi-chevron-right",
                    order=i,
                )
            )
    except OperationalError:
        # Tables might not exist yet during migrations or early initialization
        logger.warning("Database table for 'ServiceCategory' not found. Skipping dynamic sidebar items.")
    except Exception:
        logger.exception("Failed to generate dynamic sidebar items for service categories")

    return items


def register_cabinet_catalog() -> None:
    """Register or re-register the catalog module in the cabinet with latest categories."""
    declare(
        module="catalog",
        space="staff",
        topbar=TopbarEntry(
            group="admin",
            label=str(_("Catalog")),
            icon="bi-journal-text",
            url=reverse_lazy("cabinet:services_list"),
            order=15,
        ),
        sidebar=get_catalog_sidebar(),
    )


# Perform initial registration only if not in migration/setup stage
if not any(
    arg in sys.argv for arg in ["migrate", "collectstatic", "makemigrations", "migrate_all_legacy", "migrate_users"]
):
    register_cabinet_catalog()
