from codex_django.cabinet import (
    SidebarItem,
    TopbarEntry,
    declare,
)
from codex_django.cabinet.registry import cabinet_registry
from core.logger import logger
from django.db import OperationalError
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from features.main.models import ServiceCategory

CATALOG_MODULE = "catalog"
CATALOG_SPACE = "staff"


def _static_sidebar() -> list[SidebarItem]:
    return [
        SidebarItem(
            label=str(_("All Services")),
            url=reverse_lazy("cabinet:services_list"),
            icon="bi-grid",
            order=1,
        )
    ]


def get_catalog_sidebar() -> list[SidebarItem]:
    """Return static items plus dynamic categories fetched from DB."""
    items = _static_sidebar()

    try:
        categories = ServiceCategory.objects.all().order_by("order", "name")
        for i, category in enumerate(categories, start=2):
            items.append(
                SidebarItem(
                    label=category.name,
                    url=reverse_lazy(
                        "cabinet:services_category",
                        kwargs={"category_slug": category.slug},
                    ),
                    icon="bi-chevron-right",
                    order=i,
                )
            )
    except OperationalError:
        logger.warning("Database not ready for ServiceCategory. Returning default sidebar.")
        return _static_sidebar()
    except Exception:
        logger.exception("Failed to build dynamic sidebar items")
        return _static_sidebar()

    return items


def refresh_catalog_categories() -> None:
    """Refresh the catalog sidebar with the current set of categories."""
    sidebar = get_catalog_sidebar()
    if _is_catalog_shell_registered():
        _update_catalog_sidebar(sidebar)
        return

    _register_shell(sidebar=sidebar)


def register_catalog_shell() -> None:
    """Register the catalog module shell with only the static sidebar.

    Safe for AppConfig.ready() — does not access the database.
    """
    sidebar = _static_sidebar()
    if _is_catalog_shell_registered():
        _update_catalog_sidebar(sidebar)
        return

    _register_shell(sidebar=sidebar)


def _is_catalog_shell_registered() -> bool:
    return CATALOG_MODULE in getattr(cabinet_registry, "_module_topbar", {})


def _update_catalog_sidebar(sidebar: list[SidebarItem]) -> None:
    cabinet_registry._sidebar[(CATALOG_SPACE, CATALOG_MODULE)] = sidebar


def _register_shell(sidebar: list[SidebarItem]) -> None:
    declare(
        module=CATALOG_MODULE,
        space=CATALOG_SPACE,
        topbar=TopbarEntry(
            group="admin",
            label=str(_("Catalog")),
            icon="bi-journal-text",
            url=reverse_lazy("cabinet:services_list"),
            order=15,
        ),
        sidebar=sidebar,
    )
