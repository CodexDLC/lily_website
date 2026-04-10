from __future__ import annotations

from typing import Any, cast

from codex_django.cabinet.context_processors import cabinet as base_cabinet
from codex_django.cabinet.notifications import notification_registry
from codex_django.cabinet.quick_access import get_enabled_staff_quick_access, parse_selected_keys
from codex_django.cabinet.registry import cabinet_registry


def _get_default_staff_module() -> str | None:
    candidates: list[tuple[int, str]] = []
    for (space, module), items in cabinet_registry._sidebar.items():
        if space != "staff" or not items:
            continue
        topbar = cabinet_registry.get_module_topbar(module)
        order = topbar.order if topbar else 999
        candidates.append((order, module))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][1]


def _is_client_cabinet_path(request: Any) -> bool:
    normalized_path = request.path.rstrip("/")
    return "/my/" in request.path or normalized_path.endswith("/my")


def cabinet(request: Any) -> dict[str, Any]:
    """Wrap the library cabinet context with project-level quick access settings."""
    context = base_cabinet(request)
    is_client_space = getattr(request, "cabinet_space", None) == "client"
    is_client_path = _is_client_cabinet_path(request)

    module_slug = cast("str", getattr(request, "cabinet_module", ""))

    if request.user.is_authenticated and (is_client_space or is_client_path):
        active_module = module_slug or "client"
        context["cabinet_space"] = "client"
        context["cabinet_active_module"] = active_module
        context["cabinet_sidebar"] = cabinet_registry.get_sidebar("client", active_module)
        context["cabinet_active_topbar"] = cabinet_registry.get_module_topbar(active_module)
        context["cabinet_settings_url"] = None

    if (
        request.user.is_authenticated
        and context.get("cabinet_space") == "staff"
        and context.get("cabinet_active_module") == "admin"
        and not context.get("cabinet_sidebar")
    ):
        default_module = _get_default_staff_module()
        if default_module:
            context["cabinet_active_module"] = default_module
            context["cabinet_sidebar"] = cabinet_registry.get_sidebar("staff", default_module)
            context["cabinet_active_topbar"] = cabinet_registry.get_module_topbar(default_module)
            custom_settings_url = cabinet_registry.get_settings_url("staff", default_module)
            if custom_settings_url:
                context["cabinet_settings_url"] = custom_settings_url

    settings_data = context.get("cabinet_settings") or {}
    selected_keys = parse_selected_keys(settings_data.get("staff_quick_access_links"))
    context["cabinet_quick_access"] = (
        get_enabled_staff_quick_access(selected_keys, request.user)
        if request.user.is_authenticated and context.get("cabinet_space") == "staff"
        else []
    )
    return context


def notifications(request: Any) -> dict[str, Any]:
    """Adds generic notification items to every template rendered inside the cabinet."""
    items = notification_registry.get_items(request)
    return {"notification_items": items, "bell_items": items}


def bell_notifications(request: Any) -> dict[str, Any]:
    """Deprecated compatibility wrapper for older settings imports."""
    return notifications(request)
