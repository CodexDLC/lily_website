from django.urls import include, path

from ..views.analytics import AnalyticsReportsView, analytics_dashboard_view
from ..views.magic_login import magic_login_view
from ..views.ops import DataMaintenanceView, WorkerOpsView
from ..views.site_settings import site_settings_tab_view, site_settings_view

system_urlpatterns = [
    path("site/settings/", site_settings_view, name="site_settings"),
    path("site/settings/<str:tab_slug>/", site_settings_tab_view, name="site_settings_tab"),
    # Analytics
    path("analytics/", analytics_dashboard_view, name="analytics_dashboard"),
    path("analytics/reports/", AnalyticsReportsView.as_view(), name="analytics_reports"),
    # Ops
    path("ops/workers/", WorkerOpsView.as_view(), name="ops_workers"),
    path("ops/maintenance/", DataMaintenanceView.as_view(), name="ops_maintenance"),
    path("ops/notifications/", include("features.notifications.urls")),
    # Auth
    path("auth/magic-login/", magic_login_view, name="magic_login"),
]
