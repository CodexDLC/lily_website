from types import SimpleNamespace

from cabinet.context_processors import cabinet
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory


def test_cabinet_uses_public_default_module_reader(monkeypatch):
    request = SimpleNamespace(
        user=SimpleNamespace(is_authenticated=True),
        path="/cabinet/",
    )
    base_context = {
        "cabinet_space": "staff",
        "cabinet_active_module": "admin",
        "cabinet_sidebar": [],
        "cabinet_settings": {},
    }

    monkeypatch.setattr("cabinet.context_processors.base_cabinet", lambda request: base_context)
    monkeypatch.setattr("cabinet.context_processors.cabinet_registry.get_default_module", lambda space: "booking")
    monkeypatch.setattr(
        "cabinet.context_processors.cabinet_registry.get_sidebar",
        lambda space, module: ["sidebar"],
    )
    monkeypatch.setattr(
        "cabinet.context_processors.cabinet_registry.get_module_topbar",
        lambda module: "topbar",
    )
    monkeypatch.setattr(
        "cabinet.context_processors.cabinet_registry.get_settings_url",
        lambda space, module: "/cabinet/settings/",
    )
    monkeypatch.setattr("cabinet.context_processors.parse_selected_keys", lambda value: [])
    monkeypatch.setattr(
        "cabinet.context_processors.get_enabled_staff_quick_access",
        lambda selected_keys, user: [],
    )

    context = cabinet(request)

    assert context["cabinet_active_module"] == "booking"
    assert context["cabinet_sidebar"] == ["sidebar"]
    assert context["cabinet_active_topbar"] == "topbar"
    assert context["cabinet_settings_url"] == "/cabinet/settings/"


def test_cabinet_context_exposes_shell_urls():
    request = RequestFactory().get("/cabinet/")
    request.user = AnonymousUser()

    context = cabinet(request)

    assert context["cabinet_site_url"] == "/"
    assert context["cabinet_client_switch_url"]
    assert context["cabinet_staff_switch_url"]
    assert context["cabinet_logout_url"]


def test_business_stats_dashboard_hides_tracking_widgets(monkeypatch):
    request = SimpleNamespace(
        user=SimpleNamespace(is_authenticated=True),
        path="/cabinet/analytics/",
    )
    base_context = {
        "cabinet_space": "staff",
        "cabinet_active_module": "business_stats",
        "cabinet_sidebar": ["dashboard"],
        "cabinet_settings": {},
        "cabinet_dashboard_widgets": [
            SimpleNamespace(context_key="top_services"),
            SimpleNamespace(context_key="tracking_total_views"),
            SimpleNamespace(context_key="tracking_views_chart"),
            SimpleNamespace(context_key="tracking_top_pages"),
        ],
    }

    monkeypatch.setattr("cabinet.context_processors.base_cabinet", lambda request: base_context)
    monkeypatch.setattr("cabinet.context_processors.parse_selected_keys", lambda value: [])
    monkeypatch.setattr(
        "cabinet.context_processors.get_enabled_staff_quick_access",
        lambda selected_keys, user: [],
    )

    context = cabinet(request)

    assert [widget.context_key for widget in context["cabinet_dashboard_widgets"]] == ["top_services"]
